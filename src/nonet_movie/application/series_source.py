from abc import ABC, abstractmethod

from nonet_movie.application.series_discovery_queue import SeriesDiscoveryQueue


class MissedSeries:
    def __init__(self, series_url: str, error: Exception):
        self.series_url = series_url
        self.error = error


class SeriesSource(ABC):
    @abstractmethod
    def find_series(self, queue: SeriesDiscoveryQueue) -> None:
        pass


class SeriesSourcesFactory(ABC):
    @abstractmethod
    def get_sources(self) -> list[SeriesSource]:
        pass