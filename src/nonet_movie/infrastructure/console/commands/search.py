import questionary
from questionary import Choice, select

from ..transformation import present_links
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
        if 0 == len(movies):
            return

        movie: Movie = select('', choices=[Choice(f'{movie.title} ({movie.year})', value=movie) for movie in movies]).ask()
        present_links(f'{movie.title} ({movie.year})', movie.links)