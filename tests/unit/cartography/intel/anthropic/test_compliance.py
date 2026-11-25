import json
from unittest.mock import MagicMock

import requests

from cartography.intel.anthropic.compliance import get_organizations
from cartography.intel.anthropic.compliance import get_settings
from cartography.intel.anthropic.compliance import transform

BASE_URL = "https://api.anthropic.com/v1"


def _response(status_code: int, body: dict) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(body).encode()
    return response


def test_get_organizations_follows_next_page():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response(200, {"data": [{"uuid": "a"}], "has_more": True, "next_page": "p2"}),
        _response(200, {"data": [{"uuid": "b"}], "has_more": False, "next_page": None}),
    ]

    # Act
    organizations = get_organizations(session, BASE_URL)

    # Assert
    assert [org["uuid"] for org in organizations] == ["a", "b"]
    assert session.get.call_args_list[1].kwargs["params"] == {"page": "p2"}


def test_get_settings_skips_an_organization_without_the_endpoint():
    # Arrange
    session = MagicMock()
    session.get.return_value = _response(404, {})

    # Act
    settings = get_settings(session, BASE_URL, "a")

    # Assert
    assert settings is None


def test_transform_maps_known_settings_and_leaves_unreported_ones_null():
    # Act
    organization = transform(
        "a",
        [
            {"name": "api_zero_data_retention_enabled", "value": False},
            {"name": "hipaa_compliance_enabled", "value": True},
        ],
    )

    # Assert
    assert organization == {
        "id": "a",
        "api_zero_data_retention_enabled": False,
        "claude_code_zero_data_retention_enabled": None,
    }
