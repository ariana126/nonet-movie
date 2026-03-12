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
            print(f"{movie.title} ({movie.year})")
            for link in movie.links:
                print(f"{link.quality} - {link.size} ({link.url})")
            print()