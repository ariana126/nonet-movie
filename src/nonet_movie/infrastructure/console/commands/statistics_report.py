from rich.console import Console
from rich.table import Table

from nonet_movie.domain import Movie, Series, Link, Season, Episode
from nonet_movie.domain.service.movie_repositoy import MovieRepository
from nonet_movie.domain.service.series_repository import SeriesRepository
from nonet_movie.infrastructure.console.command import ConsoleCommand
from nonet_movie.infrastructure.console.presentation import TerminalPresenter


class ShowStatisticsReportCommand(ConsoleCommand):
    def __init__(self, movie_repository: MovieRepository, series_repository: SeriesRepository, presenter: TerminalPresenter) -> None:
        self.__movie_repository = movie_repository
        self.__series_repository = series_repository
        self.__presenter = presenter

    @staticmethod
    def description() -> str:
        return 'See statistics'

    def execute(self) -> None:
        self.__presenter.start_timer()
        movies: list[Movie] = self.__movie_repository.search_in_title('')
        movie_links: list[Link] = self.__get_movies_links(movies)
        series: list[Series] = self.__series_repository.search_in_title('')
        seasons: list[Season] = self.__get_seasons(series)
        episodes: list[Episode] = self.__get_episodes(seasons)
        episodes_links: list[Link] = self.__get_episode_link(episodes)
        self.__presenter.stop_timer()

        console = Console()

        table = Table(title='Movies Summary')
        table.add_column("Total movies")
        table.add_column("Total links")
        table.add_row(str(len(movies)), str(len(movie_links)))
        console.print(table, justify="center")

        table = Table(title='Series Summary')
        table.add_column("Total seris")
        table.add_column("Total seasons")
        table.add_column("Total episodes")
        table.add_column("Total links")
        table.add_row(str(len(series)), str(len(seasons)), str(len(episodes)), str(len(episodes_links)))
        console.print(table, justify="center")

    @staticmethod
    def __get_movies_links(movies: list[Movie]) -> list[Link]:
        links: list[Link] = []
        for movie in movies:
            for link in movie.links:
                links.append(link)
        return links

    @staticmethod
    def __get_seasons(series: list[Series]) -> list[Season]:
        seasons: list[Season] = []
        for s in series:
            for season in s.seasons:
                seasons.append(season)
        return seasons

    @staticmethod
    def __get_episodes(seasons: list[Season]) -> list[Episode]:
        episodes: list[Episode] = []
        for season in seasons:
            for episode in season.episodes:
                episodes.append(episode)
        return episodes

    @staticmethod
    def __get_episode_link(episodes: list[Episode]) -> list[Link]:
        links: list[Link] = []
        for episode in episodes:
            for link in episode.links:
                links.append(link)
        return links