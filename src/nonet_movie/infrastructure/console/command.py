from abc import ABC, abstractmethod


class Command(ABC):
    @staticmethod
    @abstractmethod
    def description() -> str:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass