from questionary import text

from src.nonet_movie.application.series_search import SearchSeriesUseCase
from src.nonet_movie.domain import Series, Season, Episode
from src.nonet_movie.infrastructure.console.command import CommandHandler
from src.nonet_movie.infrastructure.console.presentation import present_links, TerminalFilesPresenter, TerminalFolder


class SearchSeriesCommandHandler(CommandHandler):
    def __init__(self, use_case: SearchSeriesUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return tuple()

    def handle(self, args: list[str]) -> None:
        name: str = text('title: ').ask()

        series_list: list[Series] = self.__use_case.execute(name)
        if 0 == len(series_list):
            return

        with TerminalFilesPresenter() as presenter:
            presenter.present_folders([
                TerminalFolder(series.title, self.__present_seasons, series.seasons, presenter)
                for series in series_list
            ])

    def __present_seasons(self, seasons: list[Season], presenter: TerminalFilesPresenter) -> None:
        presenter.present_folders([
            TerminalFolder(season.number.as_string, self.__present_episodes, season.episodes, presenter)
            for season in seasons
        ])

    @staticmethod
    def __present_episodes(episodes: list[Episode], presenter: TerminalFilesPresenter) -> None:
        presenter.present_folders([
            TerminalFolder(episode.number.as_string, present_links, episode.id.as_string, episode.links)
            for episode in episodes
        ])
