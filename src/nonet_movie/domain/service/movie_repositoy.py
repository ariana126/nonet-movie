from abc import ABC, abstractmethod

from ddd.domain.value import Identity

from src.nonet_movie.domain.movie import Movie
from src.nonet_movie.domain.service.base_repository import TransactionalRepository


class MovieRepository(TransactionalRepository, ABC):
    @abstractmethod
    def search_in_title(self, title: str) -> list[Movie]:
        pass

    @abstractmethod
    def find(self, id_: Identity) -> Movie|None:
        pass

    @abstractmethod
    def save(self, movie: Movie) -> None:
        pass