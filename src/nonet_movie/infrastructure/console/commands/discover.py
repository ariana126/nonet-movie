from datetime import datetime
from rich.console import Console
from rich.table import Table

from nonet_movie.application.discovery import DiscoverNewMoviesUseCase, DiscoveryReport
from nonet_movie.infrastructure.console.command import Command
from nonet_movie.infrastructure.console.presentation import TerminalPresenter


class DiscoverCommand(Command):
    def __init__(self, use_case: DiscoverNewMoviesUseCase, presenter: TerminalPresenter):
        self.__use_case = use_case
        self.__presenter = presenter

    @staticmethod
    def description() -> str:
        return 'Add new movies'

    def execute(self) -> None:
        self.__presenter.start_timer()

        started_at: datetime = datetime.now()
        report: DiscoveryReport = self.__use_case.execute()
        finished_at: datetime = datetime.now()

        self.__presenter.stop_timer()

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

        if report.has_missed_movies:
            table = Table(title='Missed Movies')
            table.add_column("url", overflow="fold")
            table.add_column("error", overflow="fold")
            for missed_movie in report.missed_movies:
                table.add_row(missed_movie.movie_url, str(missed_movie.error))
            console.print(table, justify="center")