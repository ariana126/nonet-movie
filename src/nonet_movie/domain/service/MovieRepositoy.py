from abc import ABC, abstractmethod

from src.nonet_movie.domain.movie import Movie


class MovieRepository(ABC):
    @abstractmethod
    def search_in_title(self, title: str) -> list[Movie]:
        pass

    @abstractmethod
    def save(self, movie: Movie) -> None:
        pass