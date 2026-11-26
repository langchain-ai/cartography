import json
from unittest.mock import Mock

import pytest
import requests

from cartography.cli import CLI
from cartography.config import Config
from cartography.intel.workshop import start_workshop_ingestion
from cartography.intel.workshop import sync_settings
from tests.data.workshop import API_KEY
from tests.data.workshop import API_URL
from tests.data.workshop import response
from tests.data.workshop import SETTINGS


def test_pagination_continues_past_short_pages(mocker):
    # Arrange
    get = mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get",
        side_effect=[
            response({"syncSettings": SETTINGS[:1]}),
            response({"sync_settings": SETTINGS[1:]}),
            response({}),
        ],
    )

    # Act
    result = sync_settings.get(API_URL, API_KEY)

    # Assert
    assert result == SETTINGS
    assert [json.loads(c.kwargs["params"]["message"]) for c in get.call_args_list] == [
        {"pageSize": 100, "page": page} for page in (1, 2, 3)
    ]
    for call in get.call_args_list:
        assert call.args == (API_URL + "/workshop.v1.WorkshopService/ListSyncSettings",)
        assert call.kwargs["headers"] == {"Authorization": API_KEY}
        assert call.kwargs["params"]["encoding"] == "json"
        assert call.kwargs["allow_redirects"] is False
        assert call.kwargs["timeout"] == (10, 60)


@pytest.mark.parametrize("payload", [{}, {"syncSettings": []}, {"sync_settings": []}])
def test_empty_read(mocker, payload):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get",
        return_value=response(payload),
    )

    # Act and assert
    assert sync_settings.get(API_URL, API_KEY) == []


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {"error": "synthetic failure"},
        {"syncSettings": None},
        {"syncSettings": {}},
        {"syncSettings": [None]},
        {"syncSettings": [{}]},
        {"syncSettings": [{"tag": ""}]},
        {"syncSettings": [{"tag": 1}]},
        {"syncSettings": [{"tag": "synthetic", "clientMode": "FUTURE"}]},
        {"syncSettings": [{"tag": "synthetic", "clientMode": True}]},
        {"syncSettings": [{"tag": "synthetic", "clientMode": 4}]},
        {"syncSettings": [{"tag": "synthetic", "clientMode": None}]},
        {
            "syncSettings": [
                {"tag": "synthetic", "clientMode": "MONITOR", "client_mode": 1}
            ]
        },
        {"syncSettings": [], "sync_settings": []},
        {"syncSettings": [], "nextPageToken": "synthetic"},
        {"syncSettings": [SETTINGS[0], SETTINGS[0]]},
    ],
)
def test_malformed_reads_fail_closed(mocker, payload):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get",
        return_value=response(payload),
    )

    # Act and assert
    with pytest.raises(ValueError):
        sync_settings.get(API_URL, API_KEY)


@pytest.mark.parametrize("status", [204, 301, 302, 401, 403, 429, 500])
def test_non_200_reads_fail(mocker, status):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get",
        return_value=response({}, status),
    )

    # Act and assert
    with pytest.raises((ValueError, requests.HTTPError)):
        sync_settings.get(API_URL, API_KEY)


@pytest.mark.parametrize("failure", [requests.Timeout(), requests.ConnectionError()])
def test_transport_failures_propagate(mocker, failure):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get", side_effect=failure
    )

    # Act and assert
    with pytest.raises(type(failure)):
        sync_settings.get(API_URL, API_KEY)


@pytest.mark.parametrize("repeat", [True, False])
def test_paging_must_terminate(mocker, repeat):
    # Arrange
    mocker.patch.object(sync_settings, "MAX_PAGES", 2)
    mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get",
        side_effect=[
            response({"syncSettings": SETTINGS[:1]}),
            response({"syncSettings": SETTINGS[:1] if repeat else SETTINGS[1:]}),
        ],
    )

    # Act and assert
    with pytest.raises(ValueError):
        sync_settings.get(API_URL, API_KEY)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "UNKNOWN_CLIENT_MODE"),
        (0, "UNKNOWN_CLIENT_MODE"),
        (1, "MONITOR"),
        (2, "LOCKDOWN"),
        (3, "STANDALONE"),
        ("LOCKDOWN", "LOCKDOWN"),
    ],
)
def test_transform_modes_and_retains_only_selected_fields(value, expected):
    # Arrange
    setting = {"tag": "global", "batchSize": 42}
    if value is not None:
        setting["clientMode"] = value

    # Act
    result = sync_settings.transform([setting], "tenant-a")

    # Assert
    assert result == [
        {
            "id": '["tenant-a","global"]',
            "tag": "global",
            "mode_id": json.dumps(["tenant-a", expected], separators=(",", ":")),
            "configured_client_mode": expected,
        }
    ]


def test_tenant_ids_are_collision_resistant():
    # Arrange
    pairs = [("a:b", "c"), ("a", "b:c"), ("tenant-a", "same"), ("tenant-b", "same")]

    # Act
    ids = [sync_settings.scoped_id(*pair) for pair in pairs]

    # Assert
    assert len(set(ids)) == len(pairs)
    assert [tuple(json.loads(value)) for value in ids] == pairs


@pytest.mark.parametrize("tenant", ["", " ", None])
def test_invalid_tenant_scope(tenant):
    # Arrange
    settings = SETTINGS

    # Act and assert
    with pytest.raises(ValueError):
        sync_settings.transform(settings, tenant)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.invalid",
        "https://user:password@example.invalid",
        "https://example.invalid/path",
        "https://example.invalid?x=y",
        "https://example.invalid#fragment",
        "https://",
    ],
)
def test_invalid_origins_never_make_requests(mocker, url):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.sync_settings.requests.get")

    # Act and assert
    with pytest.raises(ValueError):
        sync_settings.get(url, API_KEY)
    get.assert_not_called()


def test_cli_wires_workshop_options(mocker, monkeypatch):
    # Arrange
    monkeypatch.setenv("SYNTHETIC_WORKSHOP_KEY", API_KEY)
    run = mocker.patch("cartography.sync.run_with_config")
    cli = CLI(Mock(), "synthetic")

    # Act
    code = cli.main(
        [
            "--neo4j-uri",
            "bolt://example.invalid",
            "--selected-modules",
            "workshop",
            "--workshop-api-url",
            API_URL,
            "--workshop-apikey-env-var",
            "SYNTHETIC_WORKSHOP_KEY",
            "--workshop-tenant-id",
            "tenant-a",
        ]
    )

    # Assert
    assert code == 0
    config = run.call_args.args[1]
    assert config.workshop_api_url == API_URL
    assert config.workshop_api_key == API_KEY
    assert config.workshop_tenant_id == "tenant-a"


def test_missing_configuration_skips_requests(mocker):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.sync_settings.requests.get")

    # Act
    start_workshop_ingestion(Mock(), Config(neo4j_uri="bolt://example.invalid"))

    # Assert
    get.assert_not_called()
