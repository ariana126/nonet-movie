from nonet_movie.application.series_source import SeriesSourcesFactory, MissedSeries
from nonet_movie.domain.series import Series
from nonet_movie.domain.service.series_repository import SeriesRepository


class SeriesDiscoveryReport:
    def __init__(self, saved_series: list[Series], missed_series: list[MissedSeries]):
        self.saved_series = saved_series
        self.missed_series = missed_series

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

    @property
    def number_of_saved_links(self) -> int:
        count: int = 0
        for series in self.saved_series:
            for season in series.seasons:
                for episode in season.episodes:
                    count += len(episode.links)
        return count

    @property
    def has_missed(self) -> bool:
        return not 0 == len(self.missed_series)

    @property
    def number_of_missed(self) -> int:
        return len(self.missed_series)


class DiscoverNewSeriesUseCase:
    def __init__(self, series_repository: SeriesRepository, series_sources_factory: SeriesSourcesFactory):
        self.__series_repository = series_repository
        self.__series_sources_factory = series_sources_factory

    def execute(self) -> SeriesDiscoveryReport:
        series: list[Series] = []
        missed_series: list[MissedSeries] = []

        for source in self.__series_sources_factory.get_sources():
            source_series, source_missed_series = source.find_series()
            series.extend(source_series)
            missed_series.extend(source_missed_series)

        self.__save_series(series)

        return SeriesDiscoveryReport(series, missed_series)

    def __save_series(self, series_list: list[Series]) -> None:
        chunk_size: int = 500
        current_chunk: int = 0

        with self.__series_repository as repository:
            for series in series_list:
                existing_series: Series = repository.find(series.id)
                if not existing_series is None:
                    existing_series.sync_seasons(series.seasons)
                    series = existing_series

                repository.save(series)
                current_chunk += 1
                if chunk_size <= current_chunk:
                    repository.flush()
                    current_chunk = 0
            repository.flush()