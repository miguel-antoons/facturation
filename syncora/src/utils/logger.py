from logging.config import dictConfig

FMT = "[%(asctime)s]  %(levelname)s : %(module)s | %(message)s"

# for adding a logger in a file import logging and
# the logger extra = logging.getLogger("extra")
# then you can use the 5 differents type of log : debug, info, warning, error, critical


def setup_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {"format": FMT}  # The default format for the logger
            },
            "handlers": {  # handlers de log in console here
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                }
            },
            "root": {"level": "DEBUG", "handlers": ["console"]},
            "loggers": {
                "extra": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagation": False,
                },
            },
        }
    )
