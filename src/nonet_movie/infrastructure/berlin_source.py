import urllib.request
from html.parser import HTMLParser

from ..application.sources import BerlinSource, MovieHasNoData
from ..domain.movie import Link, FileSize, Movie


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
        return self._rows[2:]


class BerlinSourceImpl(BerlinSource):
    def __init__(self, base_url: str):
        self.__base_url = base_url

    def get_years(self) -> list[int]:
        table: list[list[str]] = self.__get_table_of_page('')
        return [int(row[0]) for row in table]


    def get_ids_of_year(self, year: int) -> list[str]:
        table: list[list[str]] = self.__get_table_of_page(f'{year}/')
        return [row[0] for row in table]

    def get_movie(self, year: int, id_: str) -> Movie:
        table: list[list[str]] = [row for row in self.__get_table_of_page(f'{year}/{id_}/') if not '-' == row[2]]
        if 0 == len(table):
            raise MovieHasNoData(f'{year}/{id_}')

        title: str = self.__extract_title(table, year)
        links: list[Link] = [
            Link(
                f'{self.__base_url}/{year}/{id_}/{row[0]}',
                self.__extract_link_version(row[0], year),
                FileSize.from_string(row[2])
            )
            for row in table
        ]
        return Movie(title, year, links)

    def __get_table_of_page(self, page_path: str) -> list[list[str]]:
        url = f"{self.__base_url}/{page_path}"
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("utf-8")
        parser = _TableParser()
        parser.feed(html)
        return parser.get_table()

    def __extract_title(self, table: list[list[str]], year: int) -> str:
        file_name: str|None = self.__find_valid_file_name(table, year)
        if file_name is None:
            return self.__normalize_file_name(table[0][0])
        return self.__normalize_file_name(file_name).split(str(year))[0].strip()

    def __extract_link_version(self, file_name: str, year: int) -> str:
        if not self.__is_file_name_valid(file_name, year):
            return self.__normalize_file_name(file_name)
        return self.__normalize_file_name(file_name).split(str(year))[1].strip()

    def __find_valid_file_name(self, table: list[list[str]], year: int) -> str | None:
        for row in table:
            if self.__is_file_name_valid(row[0], year):
                return row[0]
        return None

    @staticmethod
    def __is_file_name_valid(file_name: str, year: int) -> bool:
        return 2 == len(file_name.split(str(year)))

    @staticmethod
    def __normalize_file_name(file_name: str) -> str:
        file_name = '.'.join(file_name.split('.')[:-1])
        file_name = file_name.replace('.', ' ')
        file_name = file_name.replace('_', ' ')
        file_name = file_name.replace('-', ' ')
        return file_name