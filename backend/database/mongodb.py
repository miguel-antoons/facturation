import contextlib
from typing import Generator

from pymongo import MongoClient
from dotenv import dotenv_values
from pymongo.synchronous.database import Database


@contextlib.contextmanager
def get_connection() -> Generator[Database]:
    mongo_uri = (
        f"mongodb://"
        f"{dotenv_values('.env')['MONGO_USER']}:"
        f"{dotenv_values('.env')['MONGO_PWD']}@"
        f"{dotenv_values('.env')['MONGO_IP']}:"
        f"{dotenv_values('.env')['MONGO_PORT']}/"
    )
    client = MongoClient(mongo_uri)
    try:
        yield client[dotenv_values('.env')['MONGO_DB']]
    finally:
        client.close()
