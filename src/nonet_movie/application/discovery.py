from underpy import ServiceClass

from .sources import BerlinSource, BerlinMovieData
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
        years_to_movies_count: dict[int, int] = {}
        failed_movies: list[dict[str, str|int]] = []

        years: list[int] = self.__berlin_source.get_years()
        years.sort(reverse=True)
        for year in years:
            ids: list[str] = self.__berlin_source.get_ids_of_year(year)
            years_to_movies_count[year] = len(ids)
            for id_ in ids:
                try:
                    movie_data: BerlinMovieData = self.__berlin_source.get_movie_data(year, id_)
                except Exception:
                    failed_movies.append({
                        'year': year,
                        'id': id_,
                        'exception': str(Exception),
                    })
                    continue
                movie = Movie(movie_data.title, year, movie_data.download_links)
                self.__movie_repository.save(movie)

        return DiscoveryReport(years_to_movies_count, failed_movies)