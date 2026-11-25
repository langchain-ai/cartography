import json
from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.openai.util import get_data_retention

URL = "https://api.openai.com/v1/organization/data_retention"


def _session(status_code: int, body: dict) -> MagicMock:
    response = requests.Response()
    response.status_code = status_code
    response.url = URL
    response._content = json.dumps(body).encode()
    session = MagicMock()
    session.get.return_value = response
    return session


def test_get_data_retention_returns_type():
    # Arrange
    session = _session(
        200, {"object": "organization.data_retention", "type": "zero_data_retention"}
    )

    # Act
    result = get_data_retention(session, URL, timeout=(1, 1))

    # Assert
    assert result == "zero_data_retention"


@pytest.mark.parametrize("status_code", [403, 404])
def test_get_data_retention_returns_none_when_unreadable(status_code):
    # Arrange
    session = _session(status_code, {})

    # Act
    result = get_data_retention(session, URL, timeout=(1, 1))

    # Assert
    assert result is None


def test_get_data_retention_raises_on_server_error():
    # Arrange
    session = _session(500, {})

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_data_retention(session, URL, timeout=(1, 1))
