from queue import Queue, Empty

from nonet_movie.domain import Series


Producer_Stopped = object()


class SeriesDiscoveryQueue:
    def __init__(self):
        self.__queue = Queue()
        self.__producers_count: int = 0
        self.__stopped_producers_count: int = 0

    def signal_producers_bind(self) -> None:
        self.__producers_count += 1

    def signal_producer_stopped(self) -> None:
        self.__queue.put(Producer_Stopped)

    def get(self) -> Series:
        message = self.__queue.get()
        if message is Producer_Stopped:
            self.__stopped_producers_count += 1
            if self.__stopped_producers_count == self.__producers_count:
                raise Empty()
            return self.get()
        return message

    def put(self, series: Series) -> None:
        self.__queue.put(series)
