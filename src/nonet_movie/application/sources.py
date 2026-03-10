from abc import ABC, abstractmethod

from ddd.domain import ValueObject

from src.nonet_movie.domain.movie import Link


class BerlinMovieData(ValueObject):
    def __init__(self, title: str, download_links: list[Link]):
        self.__title = title
        self.__download_links = download_links

    @property
    def title(self) -> str:
        return self.__title

    @property
    def download_links(self) -> list[Link]:
        return self.__download_links

class BerlinSource(ABC):
    @abstractmethod
    def get_years(self) -> list[int]:
        pass

    @abstractmethod
    def get_ids_of_year(self, year: int) -> list[str]:
        pass

    @abstractmethod
    def get_movie_data(self, year: int, id_: str) -> BerlinMovieData:
        pass