from queue import Queue, Empty

from nonet_movie.domain import Movie


Producer_Stopped = object()


class DiscoveryQueue:
    def __init__(self):
        self.__queue = Queue()
        self.__producers_count: int = 0
        self.__stopped_producers_count: int = 0

    def signal_producers_bind(self) -> None:
        self.__producers_count += 1

    def signal_producer_stopped(self) -> None:
        self.__queue.put(Producer_Stopped)

    def get(self) -> Movie:
        message = self.__queue.get()
        if message is Producer_Stopped:
            self.__stopped_producers_count += 1
            if self.__stopped_producers_count == self.__producers_count:
                raise Empty()
            return self.get()
        return message

    def put(self, movie: Movie) -> None:
        self.__queue.put(movie)

    def task_done(self):
        self.__queue.task_done()