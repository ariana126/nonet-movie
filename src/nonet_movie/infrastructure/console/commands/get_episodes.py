from ddd.domain.value import Identity
from rich.console import Console
from rich.table import Table

from src.nonet_movie.application.series_search import GetSeasonEpisodesUseCase
from src.nonet_movie.domain import SeasonNumber
from src.nonet_movie.infrastructure.console.command import CommandHandler


class GetEpisodeCommandHandler(CommandHandler):
    def __init__(self, get_episodes_use_case: GetSeasonEpisodesUseCase) -> None:
        self.__use_case = get_episodes_use_case

    @property
    def args(self) -> tuple[str, ...]:
        return 'series_id', 'season_number'

    def handle(self, args: list[str]) -> None:
        series_id = Identity.from_string(args[0])
        season_number = SeasonNumber.from_string(args[1])

        episodes = self.__use_case.execute(series_id, season_number)
        if 0 == len(episodes):
            return

        console = Console()

        for episode in episodes:
            table = Table(title=f"{episode.number}", title_justify="left")
            table.add_column("version", style="cyan")
            table.add_column("size", style="magenta")
            table.add_column("url", overflow="fold", style="green")

            for link in episode.links:
                table.add_row(link.version, link.size.as_string, link.url)

            console.print(table, justify="center")