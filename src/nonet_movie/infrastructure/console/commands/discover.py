import threading
import time
from datetime import datetime, timedelta
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
        self.__start_timer()

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

        if report.has_missed_movies:
            table = Table(title='Missed Movies')
            table.add_column("url")
            table.add_column("error")
            for missed_movie in report.missed_movies:
                table.add_row(missed_movie.movie_url, str(missed_movie.error))
            console.print(table, justify="center")

    @staticmethod
    def __start_timer() -> None:
        console = Console()

        def timer():
            start = time.perf_counter()
            while True:
                elapsed = time.perf_counter() - start
                formatted_time = str(timedelta(seconds=elapsed))
                console.print(f"[bold cyan][/bold cyan]{formatted_time}", end="\r")
                time.sleep(0.01)

        t = threading.Thread(target=timer, daemon=True)
        t.start()