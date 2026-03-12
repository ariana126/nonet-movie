from rich.console import Console
from rich.table import Table

from ....application.search import SearchMovieUseCase
from ....domain.movie import Movie
from ....infrastructure.console.command import CommandHandler


class SearchCommandHandler(CommandHandler):
    def  __init__(self, use_case: SearchMovieUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return ('name',)

    def handle(self, args: list[str]) -> None:
        name: str = args[0]

        movies: list[Movie] = self.__use_case.execute(name)
        for movie in movies:
            self.__present_movie(movie)

    @staticmethod
    def __present_movie(movie: Movie) -> None:
        console = Console()
        table = Table(title=f"{movie.title} ({movie.year})")

        table.add_column("version", justify="left", style="cyan")
        table.add_column("size", style="magenta")
        table.add_column("url", justify="left", style="green")

        for link in movie.links:
            table.add_row(link.version, link.size.as_string, link.url)

        console.print(table)