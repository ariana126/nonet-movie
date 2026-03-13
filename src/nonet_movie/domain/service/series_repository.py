from abc import ABC, abstractmethod

from ddd.domain.value import Identity

from src.nonet_movie.domain.series import Series
from src.nonet_movie.domain.service.base_repository import TransactionalRepository


class SeriesRepository(TransactionalRepository, ABC):
    @abstractmethod
    def find(self, id_: Identity) -> Series|None:
        pass

    @abstractmethod
    def save(self, series: Series) -> None:
        pass

    @abstractmethod
    def search_in_title(self, title: str) -> list[Series]:
        pass