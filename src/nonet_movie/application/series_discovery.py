import logging
from queue import Empty
from threading import Thread

from nonet_movie.application.series_discovery_queue import SeriesDiscoveryQueue
from nonet_movie.application.series_source import SeriesSourcesFactory
from nonet_movie.domain.series import Series
from nonet_movie.domain.service.series_repository import SeriesRepository


logger = logging.getLogger('DiscoverNewSeriesUseCase')


class SeriesDiscoveryReport:
    pass


class DiscoverNewSeriesUseCase:
    def __init__(self, series_repository: SeriesRepository, series_sources_factory: SeriesSourcesFactory):
        self.__series_repository = series_repository
        self.__series_sources_factory = series_sources_factory

    def execute(self) -> SeriesDiscoveryReport:
        queue = SeriesDiscoveryQueue()
        for i, source in enumerate(self.__series_sources_factory.get_sources()):
            thread_name: str = f'SeriesSource-{i}'
            Thread(target=source.find_series, args=(queue,), name=thread_name, daemon=True).start()
            queue.signal_producers_bind()

        chunk_size: int = 1000
        current_chunk: int = 0
        with self.__series_repository as repository:
            while True:
                try:
                    series: Series = queue.get()
                except Empty:
                    break

                repository.save(series)
                logger.info(f'Saved series: {series.id}')
                current_chunk += 1
                if chunk_size <= current_chunk:
                    repository.flush()
                    current_chunk = 0

        return SeriesDiscoveryReport()