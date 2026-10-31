import logging
from logging.config import dictConfig

FMT = "[%(asctime)s]  %(levelname)s : %(name)s | %(message)s"


def setup_logging() -> None:
    """Configure console-only logging for the whole application.

    Must be called once at application startup (see app.py).
    """
    dictConfig(
        {
            "version": 1,
            # Module loggers are created at import time, before this runs:
            # do not disable them, they must propagate to the root logger.
            "disable_existing_loggers": False,
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
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger named `name`, configured by setup_logging().

    Usage in any module:

        from utils.logger import get_logger

        logger = get_logger(__name__)

        logger.info("Something happened: %s", value)

    Then you can use the 5 different types of log:
    debug, info, warning, error, critical.
    """
    return logging.getLogger(name)
