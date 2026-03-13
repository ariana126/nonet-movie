from questionary import Choice, select

from src.nonet_movie.application.series_search import SearchSeriesUseCase
from src.nonet_movie.domain import Series, Season, Episode
from src.nonet_movie.infrastructure.console.command import CommandHandler
from src.nonet_movie.infrastructure.console.transformation import present_links


class SearchSeriesCommandHandler(CommandHandler):
    def __init__(self, use_case: SearchSeriesUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return ('name',)

    def handle(self, args: list[str]) -> None:
        name: str = args[0]

        series_list: list[Series] = self.__use_case.execute(name)
        if 0 == len(series_list):
            return

        series: Series = select('', choices=[Choice(s.title, value=s) for s in series_list]).ask()
        season: Season = select('', choices=[Choice(season.number.as_string, value=season) for season in series.seasons]).ask()
        episode: Episode = select('', choices=[Choice(episode.number.as_string, value=episode) for episode in season.episodes]).ask()

        present_links(episode.id.as_string, episode.links)