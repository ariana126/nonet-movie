import logging
import re
from html.parser import HTMLParser
from queue import Queue, Empty
from threading import Thread, current_thread
from typing import Any
from urllib.parse import urlparse

from curl_cffi import requests, CurlOpt

from nonet_movie.application.discovery_queue import DiscoveryQueue
from nonet_movie.application.movie_source import MovieSource
from nonet_movie.application.series_discovery_queue import SeriesDiscoveryQueue
from nonet_movie.application.series_source import SeriesSource, MissedSeries
from nonet_movie.domain import Movie, Link, FileSize
from nonet_movie.domain.series import Series, Episode, SeasonNumber, Season, EpisodeNumber


logger = logging.getLogger('AlmasMovieSource')


class PageHasInvalidSeriesData(RuntimeError):
    def __init__(self):
        super().__init__("Page has invalid series data")


class CouldNotParseEpisodeNumber(RuntimeError):
    def __init__(self):
        super().__init__("Could not parse episode number")


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
        raise CouldNotParseEpisodeNumber()


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
    def __init__(self, base_url: str, path: str, table: AlmasMovieFileServerTable):
        self.base_url = base_url
        self.path = path
        self.table = table

    @property
    def url(self) -> str:
        return f'{self.base_url}{self.path}'

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

    def find_movies(self, movies_queue: DiscoveryQueue) -> None:
        pages_queue = Queue()

        file_servers = [AlmasMovieFileServer(base_url[0], base_url[1]) for base_url in self.__movie_file_servers_base_url]
        for i, file_server in enumerate(file_servers):
            thread_name: str = f'{current_thread().name}-FileServer-{i}'
            Thread(target=self.__find_file_pages_from_file_server, args=(file_server, pages_queue), name=thread_name).start()

        finished_threads: int = 0
        while True:
            page: AlmasMovieFileServerPage | None = pages_queue.get()
            if page is None:
                finished_threads += 1
                if len(file_servers) == finished_threads:
                    movies_queue.signal_producer_stopped()
                    break
                continue

            links: list[Link] = [
                Link(
                    f'{page.url}/{row.name}',
                    page.extract_movie_version_from_file_name(row.normalized_file_name),
                    FileSize.from_string(row.size)
                )
                for row in page.table.file_rows
            ]
            movie = Movie(page.movie_title, int(page.movie_year), links)
            movies_queue.put(movie)
            logger.debug(f'Thread {current_thread().name} found movie: {movie.id}')

        logger.debug(f'Thread {current_thread().name} exiting')

    def find_series(self, series_queue: SeriesDiscoveryQueue) -> None:
        pages_queue = Queue()

        file_servers = [AlmasMovieFileServer(base_url[0], base_url[1]) for base_url in self.__series_file_servers_base_url]
        for i, file_server in enumerate(file_servers):
            thread_name: str = f'{current_thread().name}-FileServer-{i}'
            Thread(target=self.__find_file_pages_from_file_server, args=(file_server, pages_queue), name=thread_name).start()

        finished_threads: int = 0
        while True:
            page: AlmasMovieFileServerPage | None = pages_queue.get()
            if page is None:
                finished_threads += 1
                if len(file_servers) == finished_threads:
                    series_queue.signal_producer_stopped()
                    break
                continue

            try:
                series = Series(page.series_title, [])
                for row in page.table.file_rows:
                    try:
                        series.add_episode_link(
                            SeasonNumber.from_string(page.season_number),
                            EpisodeNumber.from_string(row.episode_number),
                            Link(
                                f'{page.url}/{row.name}',
                                page.episodes_version,
                                FileSize.from_string(row.size)
                            )
                        )
                    except Exception as error:
                        logger.exception(error, extra={'url': f'{page.url}/{row.name}'})
                        continue
                series_queue.put(series)
            except Exception as error:
                logger.exception(error, extra={'url': page.url})
                continue

        logger.debug(f'Thread {current_thread().name} exiting')

    @staticmethod
    def __find_file_pages_from_file_server(file_server: AlmasMovieFileServer, pages_queue: Queue) -> None:
        queue = Queue()

        def worker() -> None:
            while True:
                try:
                    path: str = queue.get(timeout=1)
                except Empty:
                    break
                try:
                    logger.debug(f'Thread {current_thread().name} processing url {file_server.base_url}{path}')
                    table: AlmasMovieFileServerTable = file_server.get_table_of_page(path)
                    if table.has_file:
                        pages_queue.put(AlmasMovieFileServerPage(file_server.base_url, path, table))
                    for folder in table.folder_rows:
                        queue.put(f"{path}/{folder.name}")
                except Exception as e:
                    logger.error(f'Thread {current_thread().name} encounters an error.', extra={'error': e, 'url': f'{file_server.base_url}{path}'})
                    logger.exception(e)
                    continue
                finally:
                    queue.task_done()

            logger.debug(f'Thread {current_thread().name} exiting')

        queue.put('')

        threads: list[Thread] = []
        for i in range(10):
            thread_name: str = f'{current_thread().name}-Crawler-{i}'
            thread = Thread(target=worker, name=thread_name)
            thread.start()
            threads.append(thread)

        queue.join()
        for thread in threads:
            thread.join()
        pages_queue.put(None)

        logger.debug(f'Thread {current_thread().name} exiting')