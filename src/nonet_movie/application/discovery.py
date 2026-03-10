from underpy import ServiceClass

from .sources import BerlinSource, BerlinMovieData
from ..domain.movie import Movie
from ..domain.service.MovieRepositoy import MovieRepository


class DiscoverNewMoviesUseCase(ServiceClass):
    def __init__(self, berlin_source: BerlinSource, movie_repository: MovieRepository):
        self.__berlin_source = berlin_source
        self.__movie_repository = movie_repository

    def execute(self) -> None:
        years: list[int] = self.__berlin_source.get_years()
        years.sort(reverse=True)
        for year in years:
            ids: list[str] = self.__berlin_source.get_ids_of_year(year)
            for id_ in ids:
                movie_data: BerlinMovieData = self.__berlin_source.get_movie_data(year, id_)
                movie = Movie(movie_data.title, year, movie_data.download_links)
                self.__movie_repository.save(movie)