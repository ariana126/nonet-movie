import logging
import shutil
import zipfile
from pathlib import Path


logger = logging.getLogger('ImportDatabaseUseCase')


class ImportDataError(Exception):
    pass


class ImportDatabaseUseCase:
    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def execute(self, file_path: str) -> None:
        """
            Import data by extracting a zip file into db_path atomically.

            Steps:
            1. Validate inputs
            2. Copy zip to db_path/../.temp/
            3. Extract all contents
            4. Remove existing db_path
            5. Rename .temp -> db_path
            """

        # ---------- Path normalization ----------
        try:
            file_path = Path(file_path).expanduser().resolve(strict=True)
        except FileNotFoundError:
            raise ImportDataError(f"No file found at {file_path}")

        db_path = Path(self.__db_path).expanduser().resolve()
        parent_dir = db_path.parent
        temp_dir = parent_dir / ".temp"

        # ---------- Validations ----------
        if not file_path.is_file():
            raise ImportDataError(f"{file_path} is not a file")

        if file_path.suffix.lower() != ".zip":
            raise ImportDataError(f"{file_path} must be a .zip file")

        if not zipfile.is_zipfile(file_path):
            raise ImportDataError(f"{file_path} is not a valid zip archive")

        # ---------- Prepare temp directory ----------
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)

        # ---------- Copy archive ----------
        copied_archive = temp_dir / file_path.name
        shutil.copy2(file_path, copied_archive)

        # ---------- Extract ----------
        try:
            with zipfile.ZipFile(copied_archive, "r") as z:
                # Basic zip-slip protection
                for member in z.namelist():
                    target_path = (temp_dir / member).resolve()
                    if not str(target_path).startswith(str(temp_dir)):
                        raise ImportDataError(f"Unsafe zip content detected: {member}")

                z.extractall(temp_dir)
        except Exception as e:
            logger.error('Failed to extract zip content', extra={'error': e})
            logger.exception(e)
            raise ImportDataError(f"Failed to extract zip file. Please try again.")
        finally:
            copied_archive.unlink(missing_ok=True)

        # ---------- Replace db_path ----------
        if db_path.exists():
            shutil.rmtree(db_path)
        temp_dir.rename(db_path)
