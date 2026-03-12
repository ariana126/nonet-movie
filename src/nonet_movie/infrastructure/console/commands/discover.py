from datetime import datetime
from rich.console import Console
from rich.table import Table

from src.nonet_movie.application.discovery import DiscoverNewMoviesUseCase, DiscoveryReport
from src.nonet_movie.infrastructure.console.command import CommandHandler


class DiscoverCommandHandler(CommandHandler):
    def __init__(self, use_case: DiscoverNewMoviesUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return tuple()

    def handle(self, args: list[str]) -> None:
        started_at: datetime = datetime.now()
        report: DiscoveryReport = self.__use_case.execute()
        finished_at: datetime = datetime.now()

        console = Console()

        table = Table(title='Discovery Completed')
        table.add_column("started at")
        table.add_column("finished at")
        table.add_column("elapsed")
        table.add_row(started_at.strftime('%Y-%m-%d %H:%M:%S'), finished_at.strftime('%Y-%m-%d %H:%M:%S'), str(finished_at - started_at))
        console.print(table, justify="center")

        table = Table(title='Summary')
        table.add_column("Total discovered")
        table.add_column("Successfully updated")
        table.add_column("Missed")
        table.add_row(str(report.total_movies_count), str(report.number_of_saved_movies), str(report.number_of_missed_movies))
        console.print(table, justify="center")