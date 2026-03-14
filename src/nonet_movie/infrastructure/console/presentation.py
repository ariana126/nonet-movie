from typing import Callable, ParamSpec, TypeVar

from prompt_toolkit.styles import Style
from questionary import select, Choice, Separator
from rich.console import Console
from rich.table import Table

from src.nonet_movie.domain import Link


def present_links(title: str, links: list[Link]) -> None:
    console = Console()
    table = Table(title=title)
    table.add_column("version", style="cyan")
    table.add_column("size", style="magenta")
    table.add_column("url", overflow="fold", style="green")
    for link in links:
        table.add_row(link.version, link.size.as_string, link.url)
    console.print(table, justify="center")


P = ParamSpec("P")
R = TypeVar("R")
class TerminalFolder:
    def __init__(self, name: str, callback: Callable[P, None], *callback_args: P.args, **callback_kwargs: P.kwargs) -> None:
        self.name = name
        self.callback = callback
        self.callback_args = callback_args
        self.callback_kwargs = callback_kwargs


class TerminalFilesPresenter:
    def __init__(self):
        self.console = Console()
        self.has_presentation_ended = False
        self.footer_keywords = [
            TerminalFolder('~ Back', self.__present_previous_folders),
            TerminalFolder('~ Exit', self.__finish_presentation),
        ]
        self.stack: list[list[TerminalFolder]] = []
        self.directory_stack: list[str] = []

    def present_folders(self, folders: list[TerminalFolder]) -> None:
        if self.has_presentation_ended:
            return
        self.stack.append(folders)

        _folders = folders.copy()
        _folders.extend(self.footer_keywords)

        choices: list[Choice] = [Choice(title=folder.name, value=folder) for folder in _folders]
        choices.insert(-2, Separator())
        folder: TerminalFolder = select(message='', choices=choices, pointer='❯', style=Style([
            ('selected', 'fg:#5f819d'),  # selected text
            ('separator', 'fg:#6C6C6C'),
            ('instruction', 'fg:#abb2bf'),
            ('pointer', 'fg:#ff6b6b bold'),
            ('highlighted', 'fg:#00d7ff bold'),
        ])).ask()

        self.console.clear()
        self.directory_stack.append(folder.name)
        self.console.print('/'.join(self.directory_stack))
        folder.callback(*folder.callback_args, **folder.callback_kwargs)
        self.present_folders([])

    def __present_previous_folders(self):
        if 2 > len(self.stack):
            self.__finish_presentation()
            return
        self.directory_stack.pop()
        self.directory_stack.pop()
        self.stack.pop()
        self.present_folders(self.stack.pop())

    def __finish_presentation(self):
        self.has_presentation_ended = True

    def __enter__(self):
        self.console.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.console.clear()