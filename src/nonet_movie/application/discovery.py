from underpy import ServiceClass

from .movie_source import MovieSourcesFactory, MovieSource, MissedMovie
from ..domain.movie import Movie
from ..domain.service.movie_repositoy import MovieRepository


class DiscoveryReport:
    def __init__(self, saved_movies: list[Movie], missed_movies: list[MissedMovie]):
        self.saved_movies = saved_movies
        self.missed_movies = missed_movies

    @property
    def total_movies_count(self) -> int:
        return len(self.saved_movies) + len(self.missed_movies)

    @property
    def number_of_saved_movies(self) -> int:
        return len(self.saved_movies)

    @property
    def number_of_missed_movies(self) -> int:
        return len(self.missed_movies)

    @property
    def has_missed_movies(self) -> bool:
        return 0 < len(self.missed_movies)


class DiscoverNewMoviesUseCase(ServiceClass):
    def __init__(self, movie_repository: MovieRepository, movie_sources_factory: MovieSourcesFactory):
        self.__movie_repository = movie_repository
        self.__movie_sources_factory = movie_sources_factory

    def execute(self) -> DiscoveryReport:
        movies: list[Movie] = []
        missed_movies: list[MissedMovie] = []

        movie_sources: list[MovieSource] = self.__movie_sources_factory.get_sources()
        for source in movie_sources:
            source_movies, source_missed_movies = source.find_movies()
            movies.extend(source_movies)
            missed_movies.extend(source_missed_movies)

        self.__save_movies(movies)

        return DiscoveryReport(movies, missed_movies)

    def __save_movies(self, movies: list[Movie]) -> None:
        chunk_size: int = 500
        current_chunk: int = 0

        with self.__movie_repository as repository:
            for movie in movies:
                existing_movie: Movie = repository.find(movie.id)
                if not existing_movie is None:
                    for link in movie.links:
                        existing_movie.add_link(link)
                    movie = existing_movie
                repository.save(movie)

                current_chunk += 1
                if chunk_size <= current_chunk:
                    repository.flush()
                    current_chunk = 0
            repository.flush()