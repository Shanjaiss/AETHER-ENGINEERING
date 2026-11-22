import json
def safe_dump(obj) -> str:
    return json.dumps(obj, default=str)
