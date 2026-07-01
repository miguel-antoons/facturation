from logging.config import dictConfig

FMT = "[%(asctime)s]  %(levelname)s | in %(module)s: %(message)s"


def setup_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "formatters": {"default": {"format": FMT}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                }
            },
            "loggers": {
                "src": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagation": False,  # éviter la remontée vers root
                },
            },
        }
    )
