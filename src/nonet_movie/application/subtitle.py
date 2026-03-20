from abc import ABC, abstractmethod

from nonet_movie.domain import Movie, Series, Subtitle


class SubtitleSource(ABC):
    @abstractmethod
    def get_subtitles_for_movie(self, movie: Movie) -> list[Subtitle]:
        pass

    @abstractmethod
    def get_subtitles_for_series(self, series: Series) -> list[Subtitle]:
        pass


class SubtitleProvider:
    def __init__(self, sources: list[SubtitleSource]):
        self.__sources = sources

    def find_movie_subtitles(self, movie: Movie) -> list[Subtitle]:
        subtitles: list[Subtitle] = []
        for source in self.__sources:
            subtitles.extend(source.get_subtitles_for_movie(movie))
        return subtitles

    def find_series_subtitles(self, series: Series) -> list[Subtitle]:
        subtitles: list[Subtitle] = []
        for source in self.__sources:
            subtitles.extend(source.get_subtitles_for_series(series))
        return subtitles