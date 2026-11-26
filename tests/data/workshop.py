import json
from typing import Any

import requests

API_URL = "https://workshop.example.invalid"
API_KEY = "synthetic-not-a-credential"
SETTINGS = [
    {"tag": "synthetic-team", "clientMode": "MONITOR"},
    {"tag": "synthetic-lab", "clientMode": "LOCKDOWN"},
]
HOSTS = [
    {
        "uuid": "synthetic-host-1",
        "hostname": "synthetic-workstation",
        "serial": "SYNTHETIC-SERIAL",
        "machineModel": "SyntheticModel",
        "osVersion": "99.1",
        "osBuild": "SYNTHETIC-BUILD",
        "santaVersion": "99.1",
        "lastSync": "2026-01-01T00:00:00Z",
        "primaryUser": "synthetic-user@example.invalid",
        "primaryUserGroups": ["synthetic-group"],
        "tags": ["synthetic-team", "synthetic-inventory-only"],
    },
]
USERS = [
    {
        "id": "synthetic-user-1",
        "username": "synthetic-user@example.invalid",
        "managerEmail": "synthetic-manager@example.invalid",
        "departmentName": "Synthetic Department",
        "costCenterName": "Synthetic Cost Center",
        "type": "DIRECTORY_TYPE_DSYNC",
    },
]
TAGS = [{"tag": "synthetic-team"}, {"tag": "synthetic-catalog-only"}]


def response(payload: Any, status: int = 200) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(payload).encode()
    result.headers["Content-Type"] = "application/json"
    return result
