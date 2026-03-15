from underpy import Fn

from src.nonet_movie.application.series_search import SearchSeriesUseCase
from src.nonet_movie.domain import Series, Season, Episode
from src.nonet_movie.infrastructure.console.command import Command
from src.nonet_movie.infrastructure.console.presentation import TerminalPresenter, TerminalMenuItem


class SearchSeriesCommand(Command):
    def __init__(self, use_case: SearchSeriesUseCase, presenter: TerminalPresenter):
        self.__use_case = use_case
        self.__presenter = presenter

    @staticmethod
    def description() -> str:
        return 'Search series'

    def execute(self) -> None:
        title: str = self.__presenter.get_user_input('title: ')

        series_list: list[Series] = self.__use_case.execute(title)
        if 0 == len(series_list):
            self.__presenter.present_not_found_page()
            return

        self.__presenter.present_menu_page(f'Founded for: {title}', [
            TerminalMenuItem(series.title, Fn(self.__present_seasons, series.seasons))
            for series in series_list
        ])


    def __present_seasons(self, seasons: list[Season]) -> None:
        if 0 == len(seasons):
            self.__presenter.present_not_found_page()
            return
        self.__presenter.present_menu([
            TerminalMenuItem(season.number.as_string, Fn(self.__present_episodes, season.episodes))
            for season in seasons
        ])

    def __present_episodes(self, episodes: list[Episode]) -> None:
        if 0 == len(episodes):
            self.__presenter.present_not_found_page()
            return
        self.__presenter.present_menu([
            TerminalMenuItem(episode.number.as_string, Fn(self.__presenter.present_links, episode.links))
            for episode in episodes
        ])
