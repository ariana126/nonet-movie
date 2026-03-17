from abc import ABC, abstractmethod

from nonet_movie.application.discovery_queue import DiscoveryQueue


class MovieSource(ABC):
    @abstractmethod
    def find_movies(self, queue: DiscoveryQueue) -> None:
        pass


class MovieSourcesFactory(ABC):
    @abstractmethod
    def get_sources(self) -> list[MovieSource]:
        pass