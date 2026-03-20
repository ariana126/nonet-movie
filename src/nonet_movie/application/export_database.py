import zipfile
from datetime import datetime
from pathlib import Path

from nonet_movie.infrastructure.persistence.json_db import JsonDB


# TODO: Decouple app use case from db implementation, which is in infrastructure.
class ExportDatabaseUseCase:
    def __init__(self, db: JsonDB):
        self.__db = db

    def execute(self) -> str:
        db_path = Path(self.__db.get_db_path()).expanduser().resolve()
        downloads_dir = Path.home() / "Downloads"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"nonet-movie-database_{timestamp}.zip"
        zip_path = downloads_dir / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for path in db_path.rglob("*"):
                if path.is_file():
                    z.write(path, arcname=path.relative_to(db_path))

        return str(zip_path)