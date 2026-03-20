from underpy import Fn

from ..presentation import TerminalPresenter, TerminalMenuItem
from ....application.search import SearchMovieUseCase
from ....domain.movie import Movie
from ....infrastructure.console.command import ConsoleCommand


class SearchMoviesCommand(ConsoleCommand):
    def  __init__(self, use_case: SearchMovieUseCase, presenter: TerminalPresenter):
        self.__use_case = use_case
        self.__presenter = presenter

    @staticmethod
    def description() -> str:
        return 'Search movies'

    def execute(self) -> None:
        title: str = self.__presenter.get_user_input('title: ')

        movies: list[Movie] = self.__use_case.execute(title)
        if 0 == len(movies):
            self.__presenter.present_not_found_page()
            return

        self.__presenter.present_menu_page(f'Founded for: {title}', [
            TerminalMenuItem(f'{movie.title} ({movie.year})', Fn(self.__present_movie_page, movie))
            for movie in movies
        ])

    def __present_movie_page(self, movie: Movie) -> None:
        self.__presenter.present_menu([
            TerminalMenuItem('Download', Fn(self.__presenter.present_links, movie.links)),
            TerminalMenuItem('Subtitles', Fn(self.__presenter.present_subtitles, movie.subtitles)),
        ])