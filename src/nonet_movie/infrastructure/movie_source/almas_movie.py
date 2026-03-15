import logging
import re
import threading
from html.parser import HTMLParser
from queue import Queue, Empty
from threading import Thread, Lock
from typing import Any
from urllib.parse import urlparse

from curl_cffi import requests, CurlOpt

from nonet_movie.application.movie_source import MovieSource, MissedMovie
from nonet_movie.application.series_source import SeriesSource, MissedSeries
from nonet_movie.domain import Movie, Link, FileSize
from nonet_movie.domain.series import Series, Episode, SeasonNumber, Season, EpisodeNumber


logger = logging.getLogger(__name__)


class MoviePageHasNoData(RuntimeError):
    def __init__(self):
        super().__init__("Movie page has no data")


class PageHasInvalidSeriesData(RuntimeError):
    def __init__(self):
        super().__init__("Page has invalid series data")


class EpisodePageHasNoData(RuntimeError):
    def __init__(self):
        super().__init__("Episodes page has no data")


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

    @property
    def episode_number(self) -> str:
        episode_number_patterns: list[str] = [r'E\d{2}', r'Ep\d{2}', r'ep\d{2}', r'E\d{2}', r'e\d{2}']
        for pattern in episode_number_patterns:
            matches = re.findall(pattern, self.name)
            if 0 < len(matches):
                return f'E{matches[0][-2:]}'
        raise RuntimeError('Could not parse episode number')


class AlmasMovieFileServerTable:
    def __init__(self, rows: list[AlmasMovieFileServerTableRow]):
        self.rows = rows

    @property
    def folder_rows(self) -> list[AlmasMovieFileServerTableRow]:
        return [row for row in self.rows[1:] if not row.is_file]

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
        return self.file_rows[0]

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
    def normalized_path_name(self) -> str:
        return self.path.replace('%20', ' ')

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
        return self.normalized_path_name.split('/')[1]

    def extract_movie_version_from_file_name(self, file_name: str) -> str:
        if not self.__can_extract_movie_data_from_file_name(file_name):
            return file_name
        return file_name.split(self.movie_year)[1].strip()

    @property
    def series_title(self) -> str:
        if 3 > len(self.__path_parts):
            raise PageHasInvalidSeriesData()
        return self.__path_parts[2]

    @property
    def season_number(self) -> str:
        if 4 > len(self.__path_parts):
            return 'S01'
        match = re.findall(r'S\d{2}', self.__path_parts[3])
        if 0 == len(match):
            return 'S01'
        return match[0]

    @property
    def episodes_version(self):
        if 3 == len(self.__path_parts):
            return 'Not Specified'
        return self.__path_parts[-1]

    @property
    def __path_parts(self) -> list[str]:
        return self.normalized_path_name.split('/')

    def __find_a_row_to_extract_movie_data(self) -> AlmasMovieFileServerTableRow | None:
        for row in self.table.file_rows:
            if self.__can_extract_movie_data_from_file_name(row.name):
                return row
        return None

    def __can_extract_movie_data_from_file_name(self, file_name: str) -> bool:
        return 2 == len(file_name.split(self.movie_year))


class AlmasMovieFileServer:
    def __init__(self, base_url: str, ip: str|None = None):
        self.base_url = base_url
        self.__ip = ip

    def get_table_of_page(self, path: str) -> AlmasMovieFileServerTable:
        if 0 < len(path) and '/' == path[0]:
            path = path[1:]
        url = f"{self.base_url}/{path}"
        url = url.replace(' ', '%20')

        options: dict[int, Any] = {CurlOpt.PROXY: "", CurlOpt.HTTPPROXYTUNNEL: 0}
        if not self.__ip is None:
            options[CurlOpt.RESOLVE] = [f"{self.__host}:{self.__ip}"]
        response = requests.get(url, curl_options=options)

        parser = _TableParser()
        parser.feed(response.text)

        return AlmasMovieFileServerTable.from_raw_data(parser.get_table())

    @property
    def __host(self) -> str:
        parsed = urlparse(self.base_url)
        port = parsed.port if parsed.port else (443 if parsed.scheme == "https" else 80)
        return f"{parsed.hostname}:{port}"


class AlmasMovieSource(MovieSource, SeriesSource):
    def __init__(self):
        self.__movie_file_servers_base_url: list[tuple[str, str]] = [
            ('https://tokyo.saymyname.website/Movies', '185.191.77.142'),
            ('https://berlin.saymyname.website/Movies', '185.137.27.122'),
            ('https://nairobi.saymyname.website/Movies', '185.137.25.102'),
        ]
        self.__series_file_servers_base_url: list[tuple[str, str]] = [
            ('https://rio.ggusers.com/Series', '87.107.102.126'),
            ('https://tokyo.ggusers.com/Series', '185.191.77.142'),
            ('https://nairobi.ggusers.com/Series', '185.137.25.102'),
        ]

    def find_movies(self) -> tuple[list[Movie], list[MissedMovie]]:
        file_servers = [AlmasMovieFileServer(base_url[0], base_url[1]) for base_url in self.__movie_file_servers_base_url]

        movies: list[Movie] = []
        missed_movies: list[MissedMovie] = []
        for file_server in file_servers:
            server_movies, server_missed_movies = self.__find_movies_from_file_server(file_server)
            movies.extend(server_movies)
            missed_movies.extend(server_missed_movies)

        return movies, missed_movies

    def find_series(self) -> tuple[list[Series], list[MissedSeries]]:
        file_servers = [AlmasMovieFileServer(base_url[0], base_url[1]) for base_url in self.__series_file_servers_base_url]

        series: list[Series] = []
        missed_series: list[MissedSeries] = []
        for file_server in file_servers:
            server_series, server_missed_series = self.__find_series_from_file_server(file_server)
            series.extend(server_series)
            missed_series.extend(server_missed_series)

        return series, missed_series

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

    def __find_series_from_file_server(self, file_server: AlmasMovieFileServer) -> tuple[list[Series], list[MissedSeries]]:
        series_map: dict[str, Series] = {}
        missed_series: list[MissedSeries] = []

        episodes_links_pages: list[AlmasMovieFileServerPage] = self.__get_pages_of_depth(file_server, 4)
        for page in episodes_links_pages:
            if not page.table.has_file:
                missed_series.append(MissedSeries(f'{file_server.base_url}{page.path}', EpisodePageHasNoData()))
                continue

            try:
                if not page.series_title in series_map:
                    series_map[page.series_title] = Series(page.series_title, [])
                series: Series = series_map[page.series_title]

                season_number = SeasonNumber.from_string(page.season_number)
                if not series.has_season_number(season_number):
                    series.add_new_season(season_number)
                season: Season = series.get_season(season_number)
            except Exception as error:
                missed_series.append(MissedSeries(f'{file_server.base_url}{page.path}', error))
                continue

            for row in page.table.file_rows:
                try:
                    episode_number = EpisodeNumber.from_string(row.episode_number)
                    if not season.has_episode_number(episode_number):
                        season.add_new_episode(episode_number)
                    episode: Episode = season.get_episode(episode_number)
                    episode.add_link(Link(
                        f'{file_server.base_url}{page.path}/{row.name}',
                        page.episodes_version,
                        FileSize.from_string(row.size)
                    ))
                except Exception as error:
                    missed_series.append(MissedSeries(f'{file_server.base_url}{page.path}/{row.name}', error))
                    continue

        return list(series_map.values()), missed_series

    @staticmethod
    def __get_pages_of_depth(file_server: AlmasMovieFileServer, depth: int, current_path: str = '') -> list[AlmasMovieFileServerPage]:
        pages: list[AlmasMovieFileServerPage] = []

        lock = Lock()
        queue = Queue()
        def worker() -> None:
            while True:
                try:
                    max_depth, path = queue.get(timeout=0.5)
                except Empty:
                    return
                try:
                    table: AlmasMovieFileServerTable = file_server.get_table_of_page(path)
                    if 0 == max_depth:
                        with lock:
                            pages.append(AlmasMovieFileServerPage(path, table))
                    else:
                        if table.has_file:
                            with lock:
                                pages.append(AlmasMovieFileServerPage(path, table))
                        for folder in table.folder_rows:
                            queue.put((max_depth - 1, f"{path}/{folder.name}"))
                except Exception as e:
                    logger.error(f'{threading.current_thread().name} encounters an error.', extra={'error': e, 'path': path})
                    logger.exception(e)
                    continue
                finally:
                    queue.task_done()

        queue.put((depth, current_path))

        threads: list[Thread] = []
        for i in range(10):
            thread = Thread(target=worker, name=f'Thread-{i}')
            thread.start()
            threads.append(thread)

        queue.join()
        for thread in threads:
            thread.join()

        return pages