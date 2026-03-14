from questionary import text

from ..presentation import present_links, TerminalFilesPresenter, TerminalFolder
from ....application.search import SearchMovieUseCase
from ....domain.movie import Movie
from ....infrastructure.console.command import CommandHandler


class SearchCommandHandler(CommandHandler):
    def  __init__(self, use_case: SearchMovieUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return tuple()

    def handle(self, args: list[str]) -> None:
        name: str = text('title: ').ask()

        movies: list[Movie] = self.__use_case.execute(name)
        if 0 == len(movies):
            return

        with TerminalFilesPresenter() as presenter:
            presenter.present_folders([
                TerminalFolder(f'{movie.title} ({movie.year})', present_links, f'{movie.title} ({movie.year})', movie.links)
                for movie in movies
            ])