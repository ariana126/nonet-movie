from nonet_movie.application.subtitle import SubtitleProvider
from nonet_movie.domain import Series, Subtitle
from nonet_movie.domain.service.series_repository import SeriesRepository


class SearchSeriesUseCase:
    def __init__(self, series_repository: SeriesRepository, subtitle_provider: SubtitleProvider):
        self.__series_repository = series_repository
        self.__subtitle_provider = subtitle_provider

    def execute(self, title: str) -> list[Series]:
        series: list[Series] = self.__series_repository.search_in_title(title)
        series.sort(key=lambda se: se.title, reverse=True)
        for s in series:
            s.seasons.sort(key=lambda season_: season_.number.as_int)
            for season in s.seasons:
                season.episodes.sort(key=lambda episode_: episode_.number.as_int)
                for episode in season.episodes:
                    episode.links.sort(key=lambda link: link.size.bytes, reverse=True)

        """
        Finding subtitles should be in discovery use case and be persisted alongside it's aggregate root (Series).
        """
        for s in series:
            subtitles: list[Subtitle] = self.__subtitle_provider.find_series_subtitles(s)
            s.add_subtitles(subtitles)

        return series