import json
from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
class Undefined:
    pass
und = Undefined()
_orig = json.JSONEncoder.default
def _my_default(self, o):
    if isinstance(o, Undefined):
        return None
    return _orig(self, o)
json.JSONEncoder.default = _my_default
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, Undefined):
            return None
        return super().default(o)
app = Flask(__name__)
app.json = CustomJSONProvider(app)
with app.app_context():
    print(jsonify({"val": und}).get_data(as_text=True))
