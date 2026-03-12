from abc import ABC, abstractmethod

from ddd.domain.value import Identity

from src.nonet_movie.domain.movie import Movie


class MovieRepository(ABC):
    @abstractmethod
    def search_in_title(self, title: str) -> list[Movie]:
        pass

    @abstractmethod
    def find(self, id_: Identity) -> Movie|None:
        pass

    @abstractmethod
    def save(self, movie: Movie) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass

    @abstractmethod
    def open_transaction(self) -> None:
        pass