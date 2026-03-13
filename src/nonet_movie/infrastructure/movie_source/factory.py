from src.nonet_movie.application.movie_source import MovieSourcesFactory, MovieSource
from src.nonet_movie.application.series_source import SeriesSourcesFactory, SeriesSource
from src.nonet_movie.infrastructure.movie_source.almas_movie import AlmasMovieSource


class MovieSourcesFactoryImpl(MovieSourcesFactory):
    def __init__(self, almas_movie_source: AlmasMovieSource) -> None:
        self.__almas_movie_source = almas_movie_source

    def get_sources(self) -> list[MovieSource]:
        return [self.__almas_movie_source]


class SeriesSourcesFactoryImpl(SeriesSourcesFactory):
    def __init__(self, almas_movie_source: AlmasMovieSource) -> None:
        self.__almas_movie_source = almas_movie_source

    def get_sources(self) -> list[SeriesSource]:
        return [self.__almas_movie_source]