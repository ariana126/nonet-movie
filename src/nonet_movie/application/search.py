from underpy import ServiceClass

from src.nonet_movie.domain.movie import Movie
from src.nonet_movie.domain.service.MovieRepositoy import MovieRepository


class SearchMovieUseCase(ServiceClass):
    def __init__(self, movie_repository: MovieRepository):
        self.__movie_repository = movie_repository

    def execute(self, title: str) -> list[Movie]:
        movies: list[Movie] = self.__movie_repository.search_in_title(title)
        movies.sort(key=lambda movie: movie.year, reverse=True)
        for movie in movies:
            movie.links.sort(key=lambda link: link.size.bytes, reverse=True)

        return movies