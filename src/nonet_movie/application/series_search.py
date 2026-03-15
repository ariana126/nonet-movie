from ddd.domain.value import Identity

from nonet_movie.domain import Series, SeasonNumber, Episode, Season, EpisodeNumber, Link
from nonet_movie.domain.service.series_repository import SeriesRepository


class SearchSeriesUseCase:
    def __init__(self, series_repository: SeriesRepository):
        self.__series_repository = series_repository

    def execute(self, title: str) -> list[Series]:
        series: list[Series] = self.__series_repository.search_in_title(title)
        series.sort(key=lambda se: se.title, reverse=True)
        for s in series:
            s.seasons.sort(key=lambda season_: season_.number.as_int)
            for season in s.seasons:
                season.episodes.sort(key=lambda episode_: episode_.number.as_int)
                for episode in season.episodes:
                    episode.links.sort(key=lambda link: link.size.bytes, reverse=True)

        return series