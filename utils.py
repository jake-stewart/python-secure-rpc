import json

def compact_json(data):
    return json.dumps(
        data,
        separators=(",", ":"),
        indent=None
    )

