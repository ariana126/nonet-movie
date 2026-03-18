import logging
from queue import Empty
from threading import Thread

from nonet_movie.application.series_discovery_queue import SeriesDiscoveryQueue
from nonet_movie.application.series_source import SeriesSourcesFactory
from nonet_movie.domain.series import Series
from nonet_movie.domain.service.series_repository import SeriesRepository


logger = logging.getLogger('DiscoverNewSeriesUseCase')


class SeriesDiscoveryReport:
    def __init__(self, saved_series: list[Series]):
        self.saved_series = saved_series

    @property
    def number_of_saved_series(self) -> int:
        return len(self.saved_series)

    @property
    def number_of_saved_seasons(self) -> int:
        count: int = 0
        for series in self.saved_series:
            count += len(series.seasons)
        return count

    @property
    def number_of_saved_episodes(self) -> int:
        count: int = 0
        for series in self.saved_series:
            for season in series.seasons:
                count += len(season.episodes)
        return count


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
                    repository.commit()
                    repository.open_transaction()
                    current_chunk = 0

        return SeriesDiscoveryReport([])