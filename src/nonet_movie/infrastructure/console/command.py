import threading
import time
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Type

from pydm import ServiceContainer
from rich.console import Console


class CommandHandler(ABC):
    @property
    @abstractmethod
    def args(self) -> tuple[str]:
        pass

    @abstractmethod
    def handle(self, args: list[str]) -> None:
        pass

    @staticmethod
    def _start_timer() -> None:
        console = Console()

        def timer():
            start = time.perf_counter()
            while True:
                elapsed = time.perf_counter() - start
                formatted_time = str(timedelta(seconds=elapsed))
                console.print(f"[bold cyan][/bold cyan]{formatted_time}", end="\r")
                time.sleep(0.01)

        t = threading.Thread(target=timer, daemon=True)
        t.start()


class ConsoleCommandHandler:
    def __init__(self, handlers: dict[str, Type[CommandHandler]]) -> None:
        self.__handlers = handlers

    def handle(self, command: str, args: list[str]) -> None:
        if not command in self.__handlers:
            raise RuntimeError(f'Command "{command}" not found.')

        handler: CommandHandler = ServiceContainer.get_instance().get_service(self.__handlers[command])

        if len(args) < len(handler.args):
            raise RuntimeError('Missing arguments.')

        handler.handle(args)