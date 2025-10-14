import jaydebeapi
from dotenv import dotenv_values


def get_connection():
    db_path = dotenv_values(".env")["DB_FILE"]
    classpath = "./ucanaccess-5.1.3-uber.jar"
    return jaydebeapi.connect(
        "net.ucanaccess.jdbc.UcanaccessDriver",
        f"jdbc:ucanaccess://{db_path};newDatabaseVersion=V2010",
        ["", ""],
        classpath
    )