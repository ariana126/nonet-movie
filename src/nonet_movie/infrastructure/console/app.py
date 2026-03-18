import logging
import sys
from typing import Type

from pydm import ServiceContainer
from underpy import Fn

from nonet_movie.infrastructure.console.command import ConsoleCommand
from nonet_movie.infrastructure.console.commands.discover_movies import DiscoverMoviesCommand
from nonet_movie.infrastructure.console.commands.discover_series import DiscoverSeriesCommand
from nonet_movie.infrastructure.console.commands.export_database import ExportDatabaseCommand
from nonet_movie.infrastructure.console.commands.import_database import ImportDatabaseCommand
from nonet_movie.infrastructure.console.commands.search_movies import SearchMoviesCommand
from nonet_movie.infrastructure.console.commands.search_series import SearchSeriesCommand
from nonet_movie.infrastructure.console.commands.database_report import ShowStatisticsReportCommand
from nonet_movie.infrastructure.console.presentation import TerminalPresenter, TerminalMenuItem, TerminalPage


class ConsoleApplication:
    def __init__(self, presenter: TerminalPresenter) -> None:
        self.__presenter = presenter
        self.__commands: list[Type[ConsoleCommand]] = [
            SearchMoviesCommand,
            SearchSeriesCommand,
            DiscoverMoviesCommand,
            DiscoverSeriesCommand,
            ShowStatisticsReportCommand,
            ExportDatabaseCommand,
            ImportDatabaseCommand,
        ]

    def run(self) -> None:
        if self.__is_health_flag_set():
            print('OK')
            return

        try:
            with self.__presenter as presenter:
                presenter.present_page(TerminalPage('Home', Fn(self.__present_home_page)))
        except Exception as exception:
            self.__handle_crash(exception)

    def __present_home_page(self):
        self.__presenter.present_welcome_message()

        commands_menu: list[TerminalMenuItem] = [
            TerminalMenuItem(command.description(), Fn(self.__execute_command, command))
            for command in self.__commands
        ]
        self.__presenter.present_menu(title='What do you want to do?', items=commands_menu)

    @staticmethod
    def __execute_command(command: Type[ConsoleCommand]) -> None:
        ServiceContainer.get_instance().get_service(command).execute()

    @staticmethod
    def __handle_crash(exception):
        print('Application crashed!')
        logger = logging.getLogger('Console Application')
        logger.critical('Application crashed!', extra={'exception': exception})
        logger.exception(exception)

    def __is_health_flag_set(self) -> bool:
        return 1 < len(sys.argv) and '--health' == sys.argv[1]