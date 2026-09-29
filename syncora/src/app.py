import logging

from flask import Flask

from routes import blueprints

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s]  %(levelname)s : %(filename)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    fapp = Flask(__name__)

    for bp in blueprints:
        fapp.register_blueprint(bp)

    return fapp


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
