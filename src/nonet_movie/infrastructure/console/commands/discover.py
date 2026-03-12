import time

from src.nonet_movie.application.discovery import DiscoverNewMoviesUseCase, DiscoveryReport
from src.nonet_movie.infrastructure.console.command import CommandHandler


class DiscoverCommandHandler(CommandHandler):
    def __init__(self, use_case: DiscoverNewMoviesUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return tuple()

    def handle(self, args: list[str]) -> None:
        print(f"Start at {time.strftime("%H:%M:%S")}")
        result: DiscoveryReport = self.__use_case.execute()
        print(f'Finish at {time.strftime("%H:%M:%S")}')

        print('Summary:')
        print(f"Total discovered: {result.total_movies_count}")
        print(f"Total failed: {result.number_of_failed_movies}")
        print(f"Number of years: {result.number_of_years}")
        print('Each year number of Movies')
        for year, movie_count in result.movies_count_in_years.items():
            print(f"Year {year}: {movie_count}")
        print('Failed movies:')
        for error in result.failed_movies:
            print(f"{error['year']}/{error['id']}")
            print(error['exception'])
            print()