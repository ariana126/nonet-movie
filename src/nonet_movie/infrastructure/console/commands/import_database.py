from nonet_movie.application.import_database import ImportDatabaseUseCase, ImportDataError
from nonet_movie.infrastructure.console.command import ConsoleCommand
from nonet_movie.infrastructure.console.presentation import TerminalPresenter


class ImportDatabaseCommand(ConsoleCommand):
    def __init__(self, use_case: ImportDatabaseUseCase, presenter: TerminalPresenter) -> None:
        self.__use_case = use_case
        self.__presenter = presenter

    @staticmethod
    def description() -> str:
        return 'Import database'

    def execute(self) -> None:
        confirm: bool = self.__presenter.confirm_with_user('Current database will be deleted. Do you want to continue?', default=False)
        if not confirm:
            return
        file_path: str = self.__presenter.get_user_input('Copy the exported file path:')

        try:
            self.__use_case.execute(file_path)
        except ImportDataError as e:
            self.__presenter.console.print(str(e))
            return

        self.__presenter.console.print('Database has been successfully imported.')