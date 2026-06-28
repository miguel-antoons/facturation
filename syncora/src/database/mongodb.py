import contextlib
from typing import TYPE_CHECKING, Any

from dotenv import dotenv_values
from pymongo import MongoClient

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

    from pymongo.synchronous.database import Database


@contextlib.contextmanager
def get_connection() -> Generator[Database[Mapping[str, Any] | Any], Any, None]:
    mongo_uri = (
        f"mongodb://"
        f"{dotenv_values('.env')['MONGO_USER']}:"
        f"{dotenv_values('.env')['MONGO_PWD']}@"
        f"{dotenv_values('.env')['MONGO_IP']}:"
        f"{dotenv_values('.env')['MONGO_PORT']}/"
    )
    client = MongoClient(mongo_uri)
    try:
        yield client[dotenv_values(".env")["MONGO_DB"]]
    finally:
        client.close()
