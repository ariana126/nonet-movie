from dotenv import load_dotenv
from pydm import ServiceContainer, EnvParametersBag

from .movie_source.factory import MovieSourcesFactoryImpl, SeriesSourcesFactoryImpl
from .persistence.json_db import JsonDB
from .persistence.json_db_movie_repository import JsonDBMovieRepository
from .persistence.json_db_series_repository import JsonDBSeriesRepository
from ..application.movie_source import MovieSourcesFactory
from ..application.series_source import SeriesSourcesFactory
from ..domain.service.movie_repositoy import MovieRepository
from ..domain.service.series_repository import SeriesRepository


def boot():
    service_container = ServiceContainer.get_instance()

    load_dotenv()
    service_container.set_parameters(EnvParametersBag())

    service_container.bind_parameters(JsonDB, {'db_path': 'JSON_DB_PATH'})

    service_container.bind(MovieRepository, JsonDBMovieRepository)
    service_container.bind(SeriesRepository, JsonDBSeriesRepository)

    service_container.bind(MovieSourcesFactory, MovieSourcesFactoryImpl)
    service_container.bind(SeriesSourcesFactory, SeriesSourcesFactoryImpl)