from flask import Flask
from routes import blueprints


def create_app():
    fapp = Flask(__name__)

    for bp in blueprints:
        fapp.register_blueprint(bp)

    return fapp

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
