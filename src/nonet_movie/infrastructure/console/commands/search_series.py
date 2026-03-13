import questionary
from questionary import Choice
from rich.console import Console, RenderableType
from rich.live import Live
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.align import Align

from src.nonet_movie.application.series_search import SearchSeriesUseCase
from src.nonet_movie.domain import Series, Season, Episode
from src.nonet_movie.infrastructure.console.command import CommandHandler


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

        series: Series = questionary.select('', choices=[Choice(s.title, value=s) for s in series_list]).ask()
        season: Season = questionary.select('', choices=[Choice(season.number.as_string, value=season) for season in series.seasons]).ask()
        episode: Episode = questionary.select('', choices=[Choice(episode.number.as_string, value=episode) for episode in season.episodes]).ask()

        console = Console()
        table = Table(title=f"{episode.id}")
        table.add_column("version", style="cyan")
        table.add_column("size", style="magenta")
        table.add_column("url", overflow="fold", style="green")
        for link in episode.links:
            table.add_row(link.version, link.size.as_string, link.url)
        console.print(table, justify="center")