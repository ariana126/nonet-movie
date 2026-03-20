from nonet_movie.application.subtitle import SubtitleProvider, SubtitleSource
from nonet_movie.infrastructure.movie_source.subzone_source import SubzoneSource


class SubtitleProviderFactory:
    @staticmethod
    def make() -> SubtitleProvider:
        sources: list[SubtitleSource] = [SubzoneSource()]
        return SubtitleProvider(sources)