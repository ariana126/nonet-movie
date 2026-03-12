import time

from src.nonet_movie.application.discovery import DiscoverNewMoviesUseCase
from src.nonet_movie.infrastructure.console.command import CommandHandler


class DiscoverCommandHandler(CommandHandler):
    def __init__(self, use_case: DiscoverNewMoviesUseCase):
        self.__use_case = use_case

    @property
    def args(self) -> tuple[str]:
        return tuple()

    def handle(self, args: list[str]) -> None:
        print(time.strftime("%H:%M:%S"))
        self.__use_case.execute()
        print(time.strftime("%H:%M:%S"))