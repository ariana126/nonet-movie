import logging
import os
from logging.handlers import RotatingFileHandler

from pythonjsonlogger import json
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


def boot() -> None:
    service_container = ServiceContainer.get_instance()

    load_dotenv()
    parameters = EnvParametersBag()
    service_container.set_parameters(parameters)

    service_container.bind_parameters(JsonDB, {'db_path': 'JSON_DB_PATH'})

    service_container.bind(MovieRepository, JsonDBMovieRepository)
    service_container.bind(SeriesRepository, JsonDBSeriesRepository)

    service_container.bind(MovieSourcesFactory, MovieSourcesFactoryImpl)
    service_container.bind(SeriesSourcesFactory, SeriesSourcesFactoryImpl)

    configure_logger(parameters.get('LOG_PATH'))


def configure_logger(log_path: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)
    formatter = json.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler = RotatingFileHandler(
        f'{log_path}/app.log',
        maxBytes=5_000_000,
        backupCount=5
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)