from ddd.domain.value import Identity

from src.nonet_movie.domain import Series, SeasonNumber, Episode, Season, EpisodeNumber, Link
from src.nonet_movie.domain.service.series_repository import SeriesRepository


class SearchSeriesUseCase:
    def __init__(self, series_repository: SeriesRepository):
        self.__series_repository = series_repository

    def execute(self, title: str) -> list[Series]:
        series: list[Series] = self.__series_repository.search_in_title(title)
        series.sort(key=lambda se: se.title, reverse=True)
        for s in series:
            s.seasons.sort(key=lambda season: season.number.as_int)

        return series


class GetSeasonEpisodesUseCase:
    def __init__(self, series_repository: SeriesRepository):
        self.__series_repository = series_repository

    def execute(self, seris_id: Identity, season_number: SeasonNumber) -> list[Episode]:
        series: Series = self.__series_repository.find(seris_id)
        if series is None:
            raise RuntimeError(f"No series found with id: {seris_id}")
        season: Season = series.get_season(season_number)
        season.episodes.sort(key=lambda episode_: episode_.number.as_int)
        for episode in season.episodes:
            episode.links.sort(key=lambda link: link.size.bytes, reverse=True)

        return season.episodes