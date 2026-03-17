import json
import os

from underpy import JSON


class JsonDB:
    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path
        self.__loaded_records: dict[str, JSON] = {}
        self.__transaction_stack_count: int = 0

    def flush(self) -> None:
        for collection_name, records in self.__loaded_records.items():
            os.makedirs(os.path.dirname(self.__collection_path(collection_name)), exist_ok=True)
            with open(self.__collection_path(collection_name), "w", encoding="utf-8") as file:
                json.dump(records, file, indent=2, ensure_ascii=False)

    def open_transaction(self) -> None:
        self.__transaction_stack_count += 1

    def close_transaction(self) -> None:
        self.__transaction_stack_count -= 1

    def load(self, collection_name: str) -> dict:
        if collection_name in self.__loaded_records:
            return self.__loaded_records[collection_name]
        if not os.path.exists(self.__collection_path(collection_name)) or os.path.getsize(self.__collection_path(collection_name)) == 0:
            return {}
        with open(self.__collection_path(collection_name), "r", encoding="utf-8") as file:
            records = json.load(file)
            self.__loaded_records[collection_name] = records
            return records

    def persist(self, records: dict, collection_name: str) -> None:
        self.__loaded_records[collection_name] = records
        if not self.__is_transaction_open:
            self.flush()

    def __collection_path(self, collection_name: str) -> str:
        return os.path.join(self.__db_path, f'{collection_name}.json')

    @property
    def __is_transaction_open(self) -> bool:
        return not 0 == self.__transaction_stack_count