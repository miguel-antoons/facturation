from flask import Flask

from routes import blueprints
from utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger("syncora")


def create_app() -> Flask:
    fapp = Flask(__name__)

    for bp in blueprints:
        fapp.register_blueprint(bp)

    return fapp


app = create_app()

if __name__ == "__main__":
    logger.info("Starting Syncora backend")
    app.run(debug=True)
