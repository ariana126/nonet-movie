from concurrent.futures import ThreadPoolExecutor, as_completed

from underpy import ServiceClass

from .sources import BerlinSource, MovieHasNoData
from ..domain.movie import Movie
from ..domain.service.MovieRepositoy import MovieRepository


class MissedMovie:
    def __init__(self, year: int, id_: str, error: Exception):
        self.year = year
        self.id_ = id_
        self.error = error


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


class DiscoverNewMoviesUseCase(ServiceClass):
    def __init__(self, berlin_source: BerlinSource, movie_repository: MovieRepository):
        self.__berlin_source = berlin_source
        self.__movie_repository = movie_repository

    def execute(self) -> DiscoveryReport:
        years: list[int] = self.__berlin_source.get_years()
        ids: dict[int, list[str]] = dict(sorted(self.__find_movie_ids(years).items(), key=lambda item: item[0], reverse=True))

        movies_data: list[Movie]
        missed_movies: list[MissedMovie]
        movies_data, missed_movies = self.__get_movies_data(ids)

        self.__save_movies(movies_data)
        return DiscoveryReport(movies_data, missed_movies)

    def __find_movie_ids(self, years: list[int]) -> dict[int, list[str]]:
        futures = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            for year in years:
                futures[year] = executor.submit(self.__berlin_source.get_ids_of_year, year)

        years_to_ids: dict[int, list[str]] = {}
        for year, future in futures.items():
            years_to_ids[year] = future.result()
        return years_to_ids

    def __get_movies_data(self, year_to_ids: dict[int, list[str]]) -> tuple[list[Movie], list[MissedMovie]]:
        futures = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            for year, ids in year_to_ids.items():
                for id_ in ids:
                    futures[executor.submit(self.__berlin_source.get_movie, year, id_)] = (year, id_)

        movies: list[Movie] = []
        failed_movies: list[MissedMovie] = []
        for future in as_completed(futures):
            year, id_ = futures[future]
            try:
                movies.append(future.result())
            except MovieHasNoData:
                pass
            except Exception as e:
                failed_movies.append(MissedMovie(year, id_, e))

        return movies, failed_movies

    def __save_movies(self, movies: list[Movie]) -> None:
        chunk_size: int = 500
        current_chunk: int = 0

        with self.__movie_repository as repository:
            for movie in movies:
                existing_movie: Movie = repository.find(movie.id())
                if not existing_movie is None:
                    for link in existing_movie.links:
                        movie.add_link(link)
                repository.save(movie)

                current_chunk += 1
                if chunk_size <= current_chunk:
                    repository.flush()
                    current_chunk = 0
            repository.flush()