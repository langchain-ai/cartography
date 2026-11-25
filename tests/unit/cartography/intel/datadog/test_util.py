import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.datadog import util
from cartography.intel.datadog.util import build_base_url
from cartography.intel.datadog.util import build_session
from cartography.intel.datadog.util import DatadogIncompleteListError
from cartography.intel.datadog.util import leak_status
from cartography.intel.datadog.util import paginated_get
from cartography.intel.datadog.util import ReadOnlySession
from tests.data.datadog.api import FakeDatadogAPI

BASE_URL = FakeDatadogAPI.base_url


def _items(count: int) -> list[dict]:
    return [{"type": "users", "id": f"id-{index:04d}"} for index in range(count)]


def _pages_requested(fake_api: FakeDatadogAPI, path: str) -> list[int]:
    return [
        params["page[number]"]
        for _, url, params in fake_api.requests
        if url == f"{BASE_URL}{path}"
    ]


@pytest.mark.parametrize("count", [0, 1, 99, 100, 101, 250, 300])
def test_paginated_get_reads_every_page(count):
    # Arrange
    fake_api = FakeDatadogAPI(paginated={"/x": _items(count)}, objects={})

    # Act
    result = paginated_get(fake_api, BASE_URL, "/x", params={"sort": "created_at"})

    # Assert
    assert [item["id"] for item in result] == [item["id"] for item in _items(count)]
    expected_pages = max(1, -(-count // util.PAGE_SIZE))
    assert _pages_requested(fake_api, "/x") == list(range(expected_pages))
    assert all(
        params["sort"] == "created_at" and params["page[size]"] == util.PAGE_SIZE
        for _, _, params in fake_api.requests
    )


@pytest.mark.parametrize("count", [0, 99, 100, 250])
def test_paginated_get_without_totals_stops_on_short_page(count):
    # Arrange
    fake_api = FakeDatadogAPI(
        paginated={"/x": _items(count)},
        objects={},
        omit_totals={"/x"},
    )

    # Act
    result = paginated_get(fake_api, BASE_URL, "/x")

    # Assert
    assert len(result) == count


def test_paginated_get_raises_when_items_fall_short_of_total():
    # Arrange
    fake_api = FakeDatadogAPI(
        paginated={"/x": _items(150)},
        objects={},
        total_overrides={"/x": 151},
    )

    # Act and assert
    with pytest.raises(DatadogIncompleteListError, match="reported a total of 151"):
        paginated_get(fake_api, BASE_URL, "/x")
    # The whole listing is retried before giving up.
    assert _pages_requested(fake_api, "/x") == [0, 1, 2] * util.LIST_ATTEMPTS


def test_paginated_get_raises_when_items_exceed_total():
    # Arrange
    fake_api = FakeDatadogAPI(
        paginated={"/x": _items(50)},
        objects={},
        total_overrides={"/x": 49},
    )

    # Act and assert
    with pytest.raises(DatadogIncompleteListError):
        paginated_get(fake_api, BASE_URL, "/x")


def test_paginated_get_raises_on_duplicate_items():
    # Arrange
    fake_api = FakeDatadogAPI(
        paginated={"/x": _items(250)},
        objects={},
        duplicate_pages={("/x", 1)},
    )

    # Act and assert
    with pytest.raises(DatadogIncompleteListError, match="more than one page"):
        paginated_get(fake_api, BASE_URL, "/x")


def test_paginated_get_raises_when_total_changes_between_pages():
    # Arrange
    responses = [
        {"data": _items(100), "meta": {"page": {"total_filtered_count": 150}}},
        {"data": _items(151)[100:], "meta": {"page": {"total_filtered_count": 151}}},
    ] * util.LIST_ATTEMPTS
    api_session = MagicMock()
    api_session.get.side_effect = [_json_response(body) for body in responses]

    # Act and assert
    with pytest.raises(DatadogIncompleteListError, match="from 150 to 151"):
        paginated_get(api_session, BASE_URL, "/x")


def test_paginated_get_retries_a_listing_that_changed():
    # Arrange
    responses = [
        {"data": _items(100), "meta": {"page": {"total_filtered_count": 150}}},
        {"data": _items(151)[100:], "meta": {"page": {"total_filtered_count": 151}}},
        {"data": _items(100), "meta": {"page": {"total_filtered_count": 151}}},
        {"data": _items(151)[100:], "meta": {"page": {"total_filtered_count": 151}}},
    ]
    api_session = MagicMock()
    api_session.get.side_effect = [_json_response(body) for body in responses]

    # Act
    result = paginated_get(api_session, BASE_URL, "/x")

    # Assert
    assert len(result) == 151


def test_paginated_get_propagates_http_errors():
    # Arrange
    fake_api = FakeDatadogAPI(
        paginated={"/x": _items(250)},
        objects={},
        failures={("/x", 1): 503},
    )

    # Act and assert
    with pytest.raises(requests.HTTPError):
        paginated_get(fake_api, BASE_URL, "/x")


def test_paginated_get_stops_at_max_pages():
    # Arrange
    api_session = MagicMock()
    api_session.get.side_effect = lambda url, params, timeout: _json_response(
        {
            "data": [
                {"id": f"{params['page[number]']}-{index}"}
                for index in range(util.PAGE_SIZE)
            ],
        },
    )

    # Act and assert
    with (
        patch.object(util, "MAX_PAGES", 3),
        patch.object(util, "LIST_ATTEMPTS", 1),
        pytest.raises(DatadogIncompleteListError, match="more than 3 pages"),
    ):
        paginated_get(api_session, BASE_URL, "/x")


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", b"POST"])
def test_read_only_session_refuses_writes(method):
    # Arrange
    session = ReadOnlySession()

    # Act and assert
    with pytest.raises(PermissionError, match="read-only"):
        session.request(method, "https://api.datadoghq.com/api/v2/users")


def test_build_session_sends_api_key_only_when_given():
    # Act
    with_api_key = build_session("api", "app")
    token_only = build_session(None, "ddsat_token")

    # Assert
    assert isinstance(with_api_key, ReadOnlySession)
    assert with_api_key.headers["DD-API-KEY"] == "api"
    assert with_api_key.headers["DD-APPLICATION-KEY"] == "app"
    assert "DD-API-KEY" not in token_only.headers
    assert token_only.headers["DD-APPLICATION-KEY"] == "ddsat_token"
    retries = with_api_key.get_adapter("https://api.datadoghq.com").max_retries
    assert list(retries.allowed_methods) == ["GET"]
    assert 429 in retries.status_forcelist


@pytest.mark.parametrize(
    ("site", "expected"),
    [
        (None, "https://api.datadoghq.com"),
        ("datadoghq.eu", "https://api.datadoghq.eu"),
        (" us5.datadoghq.com/ ", "https://api.us5.datadoghq.com"),
        ("https://proxy.example.com/dd/", "https://proxy.example.com/dd"),
    ],
)
def test_build_base_url(site, expected):
    assert build_base_url(site) == expected


def test_build_base_url_rejects_plain_http():
    with pytest.raises(ValueError, match="HTTPS"):
        build_base_url("http://api.datadoghq.com")


@pytest.mark.parametrize(
    ("relationships", "expected"),
    [
        ({}, None),
        ({"leak_information": {"data": None}}, False),
        ({"leak_information": {"data": {"id": "leak", "type": "leaked_keys"}}}, True),
    ],
)
def test_leak_status(relationships, expected):
    assert leak_status({"id": "k", "relationships": relationships}) is expected


def _json_response(body: dict) -> requests.Response:
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(body).encode()
    return response
