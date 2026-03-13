from rich.console import Console
from rich.table import Table

from src.nonet_movie.application.series_search import SearchSeriesUseCase
from src.nonet_movie.domain import Series
from src.nonet_movie.infrastructure.console.command import CommandHandler


class SearchSeriesCommandHandler(CommandHandler):
    def __init__(self, use_case: SearchSeriesUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return ('name',)

    def handle(self, args: list[str]) -> None:
        name: str = args[0]

        series: list[Series] = self.__use_case.execute(name)
        if 0 == len(series):
            return

        console = Console()

        table = Table(title=f"Series")
        table.add_column("title", justify="left", style="magenta")
        table.add_column("seasons", style="cyan")

        for s in series:
            table.add_row(s.title, ', '.join([season.number.as_string for season in s.seasons]))

        console.print(table, justify="center")