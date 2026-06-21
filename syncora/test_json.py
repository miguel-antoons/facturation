import json
class Undefined:
    pass
und = Undefined()
_orig = json.JSONEncoder.default
def _my_default(self, o):
    if isinstance(o, Undefined):
        return None
    return _orig(self, o)
json.JSONEncoder.default = _my_default
print(json.dumps(und))
