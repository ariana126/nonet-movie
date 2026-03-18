import logging
from queue import Empty
from threading import Thread

from nonet_movie.application.discovery_queue import DiscoveryQueue
from underpy import ServiceClass

from .movie_source import MovieSourcesFactory, MovieSource
from ..domain.movie import Movie
from ..domain.service.movie_repositoy import MovieRepository


logger = logging.getLogger('DiscoverNewMoviesUseCase')


class DiscoveryReport:
    def __init__(self, saved_movies: list[Movie]):
        self.saved_movies = saved_movies

    @property
    def count_of_saved_movies(self) -> int:
        return len(self.saved_movies)

class DiscoverNewMoviesUseCase(ServiceClass):
    def __init__(self, movie_repository: MovieRepository, movie_sources_factory: MovieSourcesFactory, queue: DiscoveryQueue):
        self.__movie_repository = movie_repository
        self.__movie_sources_factory = movie_sources_factory
        self.__queue = queue

    def execute(self) -> DiscoveryReport:
        movies: list[Movie] = []

        movie_sources: list[MovieSource] = self.__movie_sources_factory.get_sources()
        for i, source in enumerate(movie_sources):
            Thread(target=source.find_movies, args=(self.__queue,), name=f'MovieSource-{i}', daemon=True).start()
            self.__queue.signal_producers_bind()

        chunk_size: int = 100
        current_chunk: int = 0
        with self.__movie_repository as repository:
            while True:
                try:
                    movie: Movie = self.__queue.get()
                except Empty:
                    break
                try:
                    repository.save(movie)
                    logger.info(f'Saved movie: {movie.id}')
                    movies.append(movie)
                    current_chunk += 1
                    if chunk_size <= current_chunk:
                        repository.flush()
                        current_chunk = 0
                except Exception as e:
                    logger.error(f'Failed to save movie: {movie.id}', extra={'error': e})
                    continue

        return DiscoveryReport(movies)