from logging.config import dictConfig

FMT = "[%(asctime)s]  %(levelname)s : %(filename)s | %(message)s"

# not used


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
                "syncora_log": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )
