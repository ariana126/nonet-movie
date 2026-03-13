from abc import ABC, abstractmethod

from src.nonet_movie.domain.series import Series

class MissedSeries:
    def __init__(self, series_url: str, error: Exception):
        self.series_url = series_url
        self.error = error


class SeriesSource(ABC):
    @abstractmethod
    def find_series(self) -> tuple[list[Series], list[MissedSeries]]:
        pass


class SeriesSourcesFactory(ABC):
    @abstractmethod
    def get_sources(self) -> list[SeriesSource]:
        pass