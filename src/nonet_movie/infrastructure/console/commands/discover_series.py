from datetime import datetime

from rich.console import Console
from rich.table import Table

from nonet_movie.application.series_discovery import DiscoverNewSeriesUseCase, SeriesDiscoveryReport
from nonet_movie.infrastructure.console.command import ConsoleCommand
from nonet_movie.infrastructure.console.presentation import TerminalPresenter


class DiscoverSeriesCommand(ConsoleCommand):
    def __init__(self, use_case: DiscoverNewSeriesUseCase, presenter: TerminalPresenter) -> None:
        self.__use_case = use_case
        self.__presenter = presenter

    @staticmethod
    def description() -> str:
        return 'Discover new series from net'

    def execute(self) -> None:
        self.__presenter.start_timer()

        started_at: datetime = datetime.now()
        report: SeriesDiscoveryReport = self.__use_case.execute()
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
        table.add_column("Total series")
        table.add_column("Total seasons")
        table.add_column("Total episodes")
        table.add_column("Total links")
        table.add_column("Total errors")
        table.add_row(str(report.number_of_saved_series), str(report.number_of_saved_seasons), str(report.number_of_saved_episodes), str(report.number_of_saved_links), str(report.number_of_missed))
        console.print(table, justify="center")

        if report.has_missed:
            table = Table(title='Errors')
            table.add_column("url", overflow="fold")
            table.add_column("message", overflow="fold")
            for missed in report.missed_series:
                table.add_row(missed.series_url, str(missed.error))
            console.print(table, justify="center")