from nonet_movie.application.export_database import ExportDatabaseUseCase
from nonet_movie.infrastructure.console.command import ConsoleCommand
from nonet_movie.infrastructure.console.presentation import TerminalPresenter


class ExportDatabaseCommand(ConsoleCommand):
    def __init__(self, use_case: ExportDatabaseUseCase, presenter: TerminalPresenter):
        self.__use_case = use_case
        self.__presenter = presenter

    @staticmethod
    def description() -> str:
        return 'Export database'

    def execute(self) -> None:
        exported_file_path: str = self.__use_case.execute()
        self.__presenter.console.print(f'Exported database at {exported_file_path}')