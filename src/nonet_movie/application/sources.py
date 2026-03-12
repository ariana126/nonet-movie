from abc import ABC, abstractmethod

from ..domain.movie import Movie


class MovieHasNoData(RuntimeError):
    pass


class BerlinSource(ABC):
    @abstractmethod
    def get_years(self) -> list[int]:
        pass

    @abstractmethod
    def get_ids_of_year(self, year: int) -> list[str]:
        pass

    @abstractmethod
    def get_movie(self, year: int, id_: str) -> Movie:
        pass