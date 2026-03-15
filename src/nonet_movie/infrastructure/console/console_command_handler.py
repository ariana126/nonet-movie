from typing import Type

from pydm import ServiceContainer

from src.nonet_movie.infrastructure.console.command import Command
from src.nonet_movie.infrastructure.console.commands.discover import DiscoverCommand
from src.nonet_movie.infrastructure.console.commands.discovery_series import DiscoverSeriesCommand
from src.nonet_movie.infrastructure.console.commands.search import SearchCommand
from src.nonet_movie.infrastructure.console.commands.search_series import SearchSeriesCommand
from src.nonet_movie.infrastructure.console.commands.statistics_report import GatherStatisticsReportCommand
from src.nonet_movie.infrastructure.console.presentation import TerminalPresenter, TerminalMenuItem, Fn, \
    TerminalPage


class ConsoleCommandHandler:
    def __init__(self, presenter: TerminalPresenter) -> None:
        self.__presenter = presenter
        self.__commands: list[Type[Command]] = [
            SearchCommand,
            SearchSeriesCommand,
            DiscoverCommand,
            DiscoverSeriesCommand,
            GatherStatisticsReportCommand,
        ]

    def handle(self) -> None:
        with self.__presenter as presenter:
            presenter.present_page(TerminalPage('Home', Fn(self.__present_home_page)))

    @staticmethod
    def execute_command(command: Type[Command]) -> None:
        ServiceContainer.get_instance().get_service(command).execute()

    def __present_home_page(self):
        self.__presenter.present_welcome_message()

        commands_menu: list[TerminalMenuItem] = [
            TerminalMenuItem(command.description(), Fn(self.execute_command, command))
            for command in self.__commands
        ]
        self.__presenter.present_menu(title='What do you want to do?', items=commands_menu)