import contextlib
from typing import Generator

import jaydebeapi
from dotenv import dotenv_values


@contextlib.contextmanager
def get_connection() -> Generator[jaydebeapi.Connection]:
    db_path = dotenv_values(".env")["DB_FILE"]
    classpath = "./ucanaccess-5.1.3-uber.jar"
    class_name = "net.ucanaccess.jdbc.UcanaccessDriver"
    db_url = f"jdbc:ucanaccess://{db_path};newDatabaseVersion=V2010"
    driver_args = ["", ""]
    connection = jaydebeapi.connect(class_name, db_url, driver_args, classpath)
    try:
        yield connection
    finally:
        connection.close()
