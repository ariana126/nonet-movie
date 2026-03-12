from abc import ABC, abstractmethod
from typing import Type

from pydm import ServiceContainer


class CommandHandler(ABC):
    @property
    @abstractmethod
    def args(self) -> tuple[str]:
        pass

    @abstractmethod
    def handle(self, args: list[str]) -> None:
        pass


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