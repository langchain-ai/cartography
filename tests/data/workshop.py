import json
from typing import Any

import requests

API_URL = "https://workshop.example.invalid"
API_KEY = "synthetic-not-a-credential"
SETTINGS = [
    {"tag": "synthetic-team", "clientMode": "MONITOR"},
    {"tag": "synthetic-lab", "clientMode": "LOCKDOWN"},
]


def response(payload: Any, status: int = 200) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(payload).encode()
    result.headers["Content-Type"] = "application/json"
    return result
