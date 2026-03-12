import urllib.request
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.nonet_movie.application.movie_source import MovieSource, MissedMovie
from src.nonet_movie.domain.movie import Movie, Link, FileSize

class MoviePageHasNoData(RuntimeError):
    def __init__(self):
        super().__init__("Movie page has no data")


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: str | None = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "tr":
            self._current_row = []
        elif tag == "td" and self._current_row is not None:
            self._current_cell = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._current_row is not None:
            self._rows.append(self._current_row)
            self._current_row = None
        elif tag == "td" and self._current_cell is not None:
            self._current_row.append(self._current_cell.strip())
            self._current_cell = None

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell += data

    def get_table(self) -> list[list[str]]:
        return self._rows[1:]


class AlmasMovieFileServerTableRow:
    def __init__(self, name: str, last_modified: str, size: str):
        self.name = name
        self.last_modified = last_modified
        self.size = size

    @property
    def is_file(self) -> bool:
        return not '-' == self.size

    @property
    def normalized_file_name(self) -> str:
        file_name = '.'.join(self.name.split('.')[:-1])
        file_name = file_name.replace('.', ' ')
        file_name = file_name.replace('_', ' ')
        file_name = file_name.replace('-', ' ')
        return file_name


class AlmasMovieFileServerTable:
    def __init__(self, rows: list[AlmasMovieFileServerTableRow]):
        self.rows = rows

    @property
    def column_name(self) -> list[str]:
        return [row.name for row in self.rows[1:]]

    @property
    def has_file(self) -> bool:
        for row in self.rows:
            if row.is_file:
                return True
        return False

    @property
    def file_rows(self) -> list[AlmasMovieFileServerTableRow]:
        return [row for row in self.rows if row.is_file]

    @property
    def first_file_row(self) -> AlmasMovieFileServerTableRow:
        if not self.has_file:
            raise RuntimeError('There is no file row in table')
        for row in self.rows:
            if row.is_file:
                return row

    @staticmethod
    def from_raw_data(raw_data: list[list[str]]) -> 'AlmasMovieFileServerTable':
        rows: list[AlmasMovieFileServerTableRow] = []
        for data in raw_data:
            rows.append(AlmasMovieFileServerTableRow(data[0], data[1], data[2]))
        return AlmasMovieFileServerTable(rows)


class AlmasMovieFileServerPage:
    def __init__(self, path: str, table: AlmasMovieFileServerTable):
        self.path = path
        self.table = table

    @property
    def movie_title(self) -> str:
        if not self.table.has_file:
            raise RuntimeError('Page does not have any file for extracting movie title')
        row: AlmasMovieFileServerTableRow|None = self.__find_a_row_to_extract_movie_data()
        if row is None:
            return self.table.first_file_row.normalized_file_name
        return row.normalized_file_name.split(self.movie_year)[0].strip()

    @property
    def movie_year(self) -> str:
        return self.path.split('/')[1]

    def extract_movie_version_from_file_name(self, file_name: str) -> str:
        if not self.__can_extract_movie_data_from_file_name(file_name):
            return file_name
        return file_name.split(self.movie_year)[1].strip()

    def __find_a_row_to_extract_movie_data(self) -> AlmasMovieFileServerTableRow | None:
        for row in self.table.rows:
            if self.__can_extract_movie_data_from_file_name(row.name):
                return row
        return None

    def __can_extract_movie_data_from_file_name(self, file_name: str) -> bool:
        return 2 == len(file_name.split(self.movie_year))


class AlmasMovieFileServer:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_table_of_page(self, path: str) -> AlmasMovieFileServerTable:
        url = f"{self.base_url}/{path}"
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("utf-8")
        parser = _TableParser()
        parser.feed(html)
        return AlmasMovieFileServerTable.from_raw_data(parser.get_table())


class AlmasMovieSource(MovieSource):
    def __init__(self, file_server_base_urls: list[str]):
        self.__file_server_base_urls = file_server_base_urls

    def find_movies(self) -> tuple[list[Movie], list[MissedMovie]]:
        file_servers = [AlmasMovieFileServer(base_url) for base_url in self.__file_server_base_urls]

        movies: list[Movie] = []
        missed_movies: list[MissedMovie] = []
        for file_server in file_servers:
            server_movies, server_missed_movies = self.__find_movies_from_file_server(file_server)
            movies.extend(server_movies)
            missed_movies.extend(server_missed_movies)

        return movies, missed_movies

    def __find_movies_from_file_server(self, file_server: AlmasMovieFileServer) -> tuple[list[Movie], list[MissedMovie]]:
        movies: list[Movie] = []
        missed_movies: list[MissedMovie] = []

        movie_pages: list[AlmasMovieFileServerPage] = self.__get_pages_of_depth(file_server, 2)
        for page in movie_pages:
            if not page.table.has_file:
                missed_movies.append(MissedMovie(f'{file_server.base_url}{page.path}', MoviePageHasNoData()))
                continue
            links: list[Link] = [
                Link(
                    f'{file_server.base_url}{page.path}/{row.name}',
                    page.extract_movie_version_from_file_name(row.normalized_file_name),
                    FileSize.from_string(row.size)
                )
                for row in page.table.file_rows
            ]
            movies.append(Movie(page.movie_title, int(page.movie_year), links))

        return movies, missed_movies

    def __get_pages_of_depth(self, file_server: AlmasMovieFileServer, depth: int, current_path: str = '') -> list[AlmasMovieFileServerPage]:
        table: AlmasMovieFileServerTable = file_server.get_table_of_page(f"{current_path}")
        if 0 == depth:
            return [AlmasMovieFileServerPage(current_path, table)]

        futures = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for name in table.column_name:
                futures.append(executor.submit(self.__get_pages_of_depth, file_server, depth - 1, f"{current_path}/{name}"))

        pages: list[AlmasMovieFileServerPage] = []
        for future in as_completed(futures):
            pages.extend(future.result())

        return pages