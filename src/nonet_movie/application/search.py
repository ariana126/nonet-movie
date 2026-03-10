from underpy import ServiceClass

from src.nonet_movie.domain.movie import Movie
from src.nonet_movie.domain.service.MovieRepositoy import MovieRepository


class SearchMovieUseCase(ServiceClass):
    def __init__(self, movie_repository: MovieRepository):
        self.__movie_repository = movie_repository

    def execute(self, title: str) -> list[Movie]:
        return self.__movie_repository.search_in_title(title)