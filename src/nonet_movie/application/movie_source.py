from abc import ABC, abstractmethod

from src.nonet_movie.domain.movie import Movie


class MissedMovie:
    def __init__(self, movie_url: str, error: Exception):
        self.movie_url = movie_url
        self.error = error


class MovieSource(ABC):
    @abstractmethod
    def find_movies(self) -> tuple[list[Movie], list[MissedMovie]]:
        pass


class MovieSourcesFactory(ABC):
    @abstractmethod
    def get_sources(self) -> list[MovieSource]:
        pass