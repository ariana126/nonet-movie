from underpy import ServiceClass

from nonet_movie.application.subtitle import SubtitleProvider
from nonet_movie.domain import Subtitle
from nonet_movie.domain.movie import Movie
from nonet_movie.domain.service.movie_repositoy import MovieRepository


class SearchMovieUseCase(ServiceClass):
    def __init__(self, movie_repository: MovieRepository, subtitle_provider: SubtitleProvider):
        self.__movie_repository = movie_repository
        self.__subtitle_provider = subtitle_provider

    def execute(self, title: str) -> list[Movie]:
        movies: list[Movie] = self.__movie_repository.search_in_title(title)
        movies.sort(key=lambda _movie: _movie.year, reverse=True)
        for movie in movies:
            movie.links.sort(key=lambda link: link.size.bytes, reverse=True)

        """
        Finding subtitles should be in discovery use case and be persisted alongside it's aggregate root (Movie).
        """
        for movie in movies:
            subtitles: list[Subtitle] = self.__subtitle_provider.find_movie_subtitles(movie)
            movie.add_subtitles(subtitles)

        return movies