import threading
import time
from datetime import timedelta

from prompt_toolkit.styles import Style
from questionary import select, Choice, Separator, text
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from underpy import Fn

from nonet_movie.domain import Link


class TerminalPage:
    def __init__(self, title: str, loader: Fn) -> None:
        self.title = title
        self.loader = loader


class TerminalMenuItem:
    def __init__(self, name: str, callback: Fn) -> None:
        self.name = name
        self.callback = callback


class TerminalPresenter:
    def __init__(self):
        self.console = Console()
        self.footer_keywords = [
            TerminalMenuItem('~ Back', Fn(self.__present_previous_page)),
            TerminalMenuItem('~ Return to home', Fn(self.__present_first_page)),
            TerminalMenuItem('~ Exit', Fn(self.__finish_presentation)),
        ]
        self.has_presentation_ended = False
        self.page_stack: list[TerminalPage] = []
        self.timer_stop_event: threading.Event = threading.Event()
        self.style = Style([
            ('qmark', 'fg:#00ffcc bold'),
            ('question', 'bold fg:#ffffff'),
            ("answer", "fg:#00ff87 bold"),
            ('selected', 'fg:#5f819d'),
            ('separator', 'fg:#6C6C6C'),
            ('instruction', 'fg:#abb2bf'),
            ('pointer', 'fg:#ff6b6b bold'),
            ('highlighted', 'fg:#00d7ff bold'),
        ])

    def present_page(self, page: TerminalPage) -> None:
        if self.has_presentation_ended:
            return
        self.page_stack.append(page)

        self.console.clear()
        self.__present_page_title()

        page.loader.call()

        if not page.loader.is_function(self.present_menu) and not self.has_presentation_ended:
            self.__present_footer_keywords()

    def present_menu_page(self, page_title: str, menu_items: list[TerminalMenuItem], menu_title: str = '') -> None:
        self.present_page(TerminalPage(page_title, Fn(self.present_menu, menu_items, menu_title)))

    def present_not_found_page(self):
        self.present_page(TerminalPage('', Fn(self.__present_not_found)))

    def present_menu(self, items: list[TerminalMenuItem], title: str = '') -> None:
        _choices: list[Choice] = self.__get_menu_choices(items)
        item: TerminalMenuItem = select(qmark='', message=title, pointer='❯', choices=_choices, style=self.style).ask()
        if self.__is_item_footer_keyword(item):
            item.callback.call()
            return
        self.present_page(TerminalPage(item.name, item.callback))

    def get_user_input(self, message: str) -> str:
        return text(qmark='', message=message, style=self.style).ask()

    def present_links(self, links: list[Link]) -> None:
        table = Table()
        table.add_column("version", style="cyan")
        table.add_column("size", style="magenta")
        table.add_column("url", overflow="fold", style="green")
        for link in links:
            table.add_row(link.version, link.size.as_string, link.url)
        self.console.print(table)

    def present_welcome_message(self):
        welcome_text = Text(justify='center')
        welcome_text.append("\nWELCOME\n", style="bold green")

        self.console.print(Panel(
            welcome_text,
            border_style="bright_blue",
            expand=False,
            padding=(0, 15),
        ))

    def start_timer(self) -> None:
        self.timer_stop_event.clear()
        def timer():
            start = time.perf_counter()
            while not self.timer_stop_event.is_set():
                elapsed = time.perf_counter() - start
                formatted_time = str(timedelta(seconds=elapsed))
                self.console.print(f"[bold cyan][/bold cyan]{formatted_time}", end="\r")
                time.sleep(0.01)

        threading.Thread(target=timer, daemon=True).start()

    def stop_timer(self) -> None:
        self.timer_stop_event.set()

    def __present_page_title(self):
        if 0 == len(self.page_stack):
            return
        title: str = self.page_stack[-1].title
        if '' == title:
            return
        self.console.print(title)

    def __present_not_found(self):
        self.console.print("[bold red]Nothing found![/bold red]", style="red")

    def __present_footer_keywords(self) -> None:
        _choices: list[Choice] = self.__get_menu_choices([])
        keyword: TerminalMenuItem = select(qmark='', message='', pointer='❯', choices=_choices, style=self.style).ask()
        keyword.callback.call()

    def __present_previous_page(self):
        if 2 > len(self.page_stack):
            self.__finish_presentation()
            return
        self.page_stack.pop()
        self.present_page(self.page_stack.pop())

    def __present_first_page(self):
        first_page: TerminalPage = self.page_stack[0]
        self.page_stack = []
        self.present_page(first_page)

    def __finish_presentation(self):
        self.has_presentation_ended = True

    def  __get_menu_choices(self, items) -> list[Choice]:
        _choices: list[Choice] = [Choice(title=item.name, value=item) for item in items]
        _choices.append(Separator())
        _choices.extend([Choice(title=keyword.name, value=keyword) for keyword in self.footer_keywords])
        return _choices

    def __is_item_footer_keyword(self, item: TerminalMenuItem) -> bool:
        for keyword in self.footer_keywords:
            if item.name == keyword.name:
                return True
        return False

    def __enter__(self):
        self.console.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.console.clear()