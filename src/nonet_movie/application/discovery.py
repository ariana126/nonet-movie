from underpy import ServiceClass

from .sources import BerlinSource, BerlinMovieData, MovieHasNoData
from ..domain.movie import Movie
from ..domain.service.MovieRepositoy import MovieRepository


class DiscoveryReport:
    def __init__(self, movies_count_in_years: dict[int, int], failed_movies: list[dict[str, str|int]]):
        self.movies_count_in_years = movies_count_in_years
        self.failed_movies = failed_movies

    @property
    def number_of_years(self) -> int:
        return len(self.movies_count_in_years)

    @property
    def total_movies_count(self) -> int:
        total: int = 0
        for count in self.movies_count_in_years.values():
            total += count
        return total

    @property
    def number_of_failed_movies(self) -> int:
        return len(self.failed_movies)

class DiscoverNewMoviesUseCase(ServiceClass):
    def __init__(self, berlin_source: BerlinSource, movie_repository: MovieRepository):
        self.__berlin_source = berlin_source
        self.__movie_repository = movie_repository

    def execute(self) -> DiscoveryReport:
        chunk_size: int = 500
        current_chunk: int = 0

        years_to_movies_count: dict[int, int] = {}
        failed_movies: list[dict[str, str|int]] = []

        years: list[int] = self.__berlin_source.get_years()
        years.sort(reverse=True)
        for year in years:
            ids: list[str] = self.__berlin_source.get_ids_of_year(year)
            years_to_movies_count[year] = 0
            for id_ in ids:
                self.__movie_repository.open_transaction()
                try:
                    movie_data: BerlinMovieData = self.__berlin_source.get_movie_data(year, id_)
                except MovieHasNoData:
                    continue
                except Exception as e:
                    years_to_movies_count[year] += 1
                    failed_movies.append({
                        'year': year,
                        'id': id_,
                        'exception': e,
                    })
                    continue
                years_to_movies_count[year] += 1

                movie = Movie(movie_data.title, year, movie_data.download_links)
                existing_movie: Movie = self.__movie_repository.find(movie.id())
                if existing_movie is not None:
                    for link in existing_movie.links:
                        movie.add_link(link)

                self.__movie_repository.save(movie)
                current_chunk += 1
                if chunk_size <= current_chunk:
                    self.__movie_repository.flush()
                    current_chunk = 0
            self.__movie_repository.flush()

        return DiscoveryReport(years_to_movies_count, failed_movies)