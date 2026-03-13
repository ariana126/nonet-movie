from abc import ABC, abstractmethod


class TransactionalRepository(ABC):
    @abstractmethod
    def flush(self) -> None:
        pass

    @abstractmethod
    def open_transaction(self) -> None:
        pass

    @abstractmethod
    def close_transaction(self) -> None:
        pass

    def __enter__(self):
        self.open_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_transaction()