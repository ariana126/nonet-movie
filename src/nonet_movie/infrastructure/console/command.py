from abc import ABC, abstractmethod


class ConsoleCommand(ABC):
    @staticmethod
    @abstractmethod
    def description() -> str:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass