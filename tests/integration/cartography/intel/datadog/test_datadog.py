import copy
from unittest.mock import patch

import pytest
import requests

import cartography.intel.datadog
from cartography.config import Config
from cartography.intel.datadog.util import DatadogIncompleteListError
from tests.data.datadog import api as fixtures
from tests.data.datadog.api import FakeDatadogAPI
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
SECOND_UPDATE_TAG = 223456789

DATADOG_LABELS = [
    "DatadogOrganization",
    "DatadogRole",
    "DatadogUser",
    "DatadogServiceAccount",
    "DatadogAPIKey",
    "DatadogApplicationKey",
    "DatadogAccessToken",
]


def _config(update_tag: int) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        datadog_api_key="fake-api-key",
        datadog_app_key="fake-app-key",
        datadog_site="datadoghq.com",
    )


def _run(neo4j_session, fake_api: FakeDatadogAPI, update_tag: int) -> None:
    with patch.object(
        cartography.intel.datadog,
        "build_session",
        return_value=fake_api,
    ):
        cartography.intel.datadog.start_datadog_ingestion(
            neo4j_session,
            _config(update_tag),
        )


def _reset(neo4j_session) -> None:
    for label in DATADOG_LABELS:
        neo4j_session.run(f"MATCH (n:{label}) DETACH DELETE n")


def _count(neo4j_session, label: str, update_tag: int | None = None) -> int:
    query = f"MATCH (n:{label})"
    if update_tag is not None:
        query += " WHERE n.lastupdated = $tag"
    query += " RETURN count(n) AS c"
    return neo4j_session.run(query, tag=update_tag).single()["c"]


def _snapshot(neo4j_session) -> dict[str, set[str]]:
    return {
        label: {
            record["id"]
            for record in neo4j_session.run(f"MATCH (n:{label}) RETURN n.id AS id")
        }
        for label in DATADOG_LABELS
    }


def _paginated_without(path: str, item_id: str) -> dict:
    paginated = copy.deepcopy(fixtures.PAGINATED_PATHS)
    paginated[path] = [item for item in paginated[path] if item["id"] != item_id]
    return paginated


def test_sync_datadog(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    fake_api = FakeDatadogAPI()

    # Act
    _run(neo4j_session, fake_api, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "DatadogOrganization",
        ["id", "name", "public_id", "api_base_url"],
    ) == {
        (fixtures.ORG_ID, "Example Corp", "abc123def", "https://api.datadoghq.com"),
    }
    assert check_nodes(neo4j_session, "DatadogRole", ["id", "name"]) == {
        (fixtures.ADMIN_ROLE_ID, "Datadog Admin Role"),
        (fixtures.STANDARD_ROLE_ID, "Datadog Standard Role"),
        (fixtures.READ_ONLY_ROLE_ID, "Datadog Read Only Role"),
        (fixtures.AUDITOR_ROLE_ID, "Key auditor"),
    }
    auditor = neo4j_session.run(
        "MATCH (r:DatadogRole {id: $id}) RETURN r.permissions AS p",
        id=fixtures.AUDITOR_ROLE_ID,
    ).single()["p"]
    assert auditor == [
        "api_keys_read",
        "org_app_keys_read",
        "perm-9999",
        "user_access_read",
    ]

    # Every page of users is read: 3 named people plus 230 generated users.
    assert _count(neo4j_session, "DatadogUser") == 3 + fixtures.GENERATED_USER_COUNT
    named_users = {
        row
        for row in check_nodes(
            neo4j_session,
            "DatadogUser",
            ["id", "email", "status", "disabled", "mfa_enabled"],
        )
        if not row[0].startswith("user-gen-")
    }
    assert named_users == {
        (fixtures.ALICE_ID, "alice@example.com", "Active", False, True),
        (fixtures.BOB_ID, "bob@example.com", "Disabled", True, False),
        (fixtures.CAROL_ID, "carol@example.com", "Pending", False, None),
    }
    assert check_nodes(
        neo4j_session,
        "DatadogServiceAccount",
        ["id", "name", "disabled"],
    ) == {
        (fixtures.CI_SA_ID, "ci-deployer", False),
        (fixtures.CARTOGRAPHY_SA_ID, "cartography-readonly", False),
    }
    assert (
        _count(neo4j_session, "DatadogUser:UserAccount")
        == 3 + fixtures.GENERATED_USER_COUNT
    )

    user_roles = {
        row
        for row in check_rels(
            neo4j_session,
            "DatadogUser",
            "id",
            "DatadogRole",
            "id",
            "HAS_ROLE",
        )
        if not row[0].startswith("user-gen-")
    }
    assert user_roles == {
        (fixtures.ALICE_ID, fixtures.ADMIN_ROLE_ID),
        (fixtures.ALICE_ID, fixtures.READ_ONLY_ROLE_ID),
        (fixtures.BOB_ID, fixtures.STANDARD_ROLE_ID),
    }
    assert check_rels(
        neo4j_session,
        "DatadogServiceAccount",
        "id",
        "DatadogRole",
        "id",
        "HAS_ROLE",
    ) == {
        (fixtures.CI_SA_ID, fixtures.STANDARD_ROLE_ID),
        (fixtures.CARTOGRAPHY_SA_ID, fixtures.AUDITOR_ROLE_ID),
    }

    assert check_nodes(
        neo4j_session,
        "DatadogAPIKey",
        ["id", "name", "last4", "leaked"],
    ) == {
        ("apikey-0001", "production-agents", "0001", False),
        ("apikey-0002", "ci-metrics", "0002", True),
    }
    assert check_rels(
        neo4j_session,
        "DatadogUser",
        "id",
        "DatadogAPIKey",
        "id",
        "CREATED",
    ) == {(fixtures.BOB_ID, "apikey-0001")}
    assert check_rels(
        neo4j_session,
        "DatadogServiceAccount",
        "id",
        "DatadogAPIKey",
        "id",
        "CREATED",
    ) == {(fixtures.CI_SA_ID, "apikey-0002")}

    assert check_nodes(
        neo4j_session,
        "DatadogApplicationKey",
        ["id", "is_scoped", "leaked"],
    ) == {
        ("appkey-0001", False, False),
        ("appkey-0002", True, False),
        ("appkey-0003", False, None),
    }
    assert check_rels(
        neo4j_session,
        "DatadogApplicationKey",
        "id",
        "DatadogUser",
        "id",
        "OWNED_BY",
    ) == {("appkey-0001", fixtures.ALICE_ID), ("appkey-0003", fixtures.BOB_ID)}
    assert check_rels(
        neo4j_session,
        "DatadogApplicationKey",
        "id",
        "DatadogServiceAccount",
        "id",
        "OWNED_BY",
    ) == {("appkey-0002", fixtures.CARTOGRAPHY_SA_ID)}

    assert check_nodes(
        neo4j_session,
        "DatadogAccessToken",
        ["id", "token_type", "expires_at"],
    ) == {
        ("pat-0001", "personal", "2026-12-01T00:00:00+00:00"),
        ("sat-0001", "service", None),
    }
    assert check_rels(
        neo4j_session,
        "DatadogAccessToken",
        "id",
        "DatadogUser",
        "id",
        "OWNED_BY",
    ) == {("pat-0001", fixtures.ALICE_ID)}
    assert check_rels(
        neo4j_session,
        "DatadogAccessToken",
        "id",
        "DatadogServiceAccount",
        "id",
        "OWNED_BY",
    ) == {("sat-0001", fixtures.CI_SA_ID)}
    assert (
        _count(neo4j_session, "DatadogAPIKey:APIKey")
        + _count(neo4j_session, "DatadogApplicationKey:APIKey")
        + _count(neo4j_session, "DatadogAccessToken:APIKey")
    ) == 7

    resource_targets = neo4j_session.run(
        """
        MATCH (:DatadogOrganization {id: $org})-[:RESOURCE]->(n)
        RETURN count(n) AS c
        """,
        org=fixtures.ORG_ID,
    ).single()["c"]
    assert resource_targets == 4 + 3 + fixtures.GENERATED_USER_COUNT + 2 + 2 + 3 + 2

    # The module sends only GET requests.
    assert {method for method, _, _ in fake_api.requests} == {"GET"}


def test_sync_datadog_stores_no_secret_values(neo4j_session):
    # Arrange
    _reset(neo4j_session)

    # Act
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)

    # Assert
    records = neo4j_session.run(
        """
        MATCH (n)
        WHERE n:DatadogAPIKey OR n:DatadogApplicationKey OR n:DatadogAccessToken
        RETURN properties(n) AS props
        """,
    )
    for record in records:
        props = record["props"]
        assert "key" not in props
        assert "public_portion" not in props
        for value in props.values():
            assert str(value) not in fixtures.FAKE_SECRETS


def test_complete_resync_removes_stale_nodes(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    paginated = _paginated_without("/api/v2/users", fixtures.BOB_ID)
    paginated["/api/v2/api_keys"] = [
        key for key in paginated["/api/v2/api_keys"] if key["id"] != "apikey-0001"
    ]

    # Act
    _run(neo4j_session, FakeDatadogAPI(paginated=paginated), SECOND_UPDATE_TAG)

    # Assert
    snapshot = _snapshot(neo4j_session)
    assert fixtures.BOB_ID not in snapshot["DatadogUser"]
    assert fixtures.ALICE_ID in snapshot["DatadogUser"]
    assert snapshot["DatadogAPIKey"] == {"apikey-0002"}
    assert _count(neo4j_session, "DatadogUser", TEST_UPDATE_TAG) == 0


@pytest.mark.parametrize(
    "fake_api",
    [
        pytest.param(
            FakeDatadogAPI(
                paginated=_paginated_without("/api/v2/users", fixtures.BOB_ID),
                failures={("/api/v2/users", 2): 500},
            ),
            id="server-error-on-last-page",
        ),
        pytest.param(
            FakeDatadogAPI(
                paginated=_paginated_without("/api/v2/users", fixtures.BOB_ID),
                failures={("/api/v2/users", 1): 429},
            ),
            id="rate-limited-mid-listing",
        ),
        pytest.param(
            FakeDatadogAPI(
                paginated=_paginated_without("/api/v2/users", fixtures.BOB_ID),
                total_overrides={"/api/v2/users": 400},
            ),
            id="fewer-items-than-reported-total",
        ),
        pytest.param(
            FakeDatadogAPI(
                paginated=_paginated_without("/api/v2/users", fixtures.BOB_ID),
                duplicate_pages={("/api/v2/users", 1)},
            ),
            id="page-shifted-during-listing",
        ),
        pytest.param(
            FakeDatadogAPI(
                paginated={**fixtures.PAGINATED_PATHS, "/api/v2/users": []},
            ),
            id="empty-user-listing",
        ),
    ],
)
def test_failed_or_partial_user_listing_keeps_graph(neo4j_session, fake_api):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    before = _snapshot(neo4j_session)

    # Act and assert
    with pytest.raises((requests.HTTPError, DatadogIncompleteListError)):
        _run(neo4j_session, fake_api, SECOND_UPDATE_TAG)

    # Assert
    assert _snapshot(neo4j_session) == before
    assert fixtures.BOB_ID in before["DatadogUser"]
    # Users, keys, and tokens were neither cleaned up nor rewritten.
    assert _count(neo4j_session, "DatadogUser", SECOND_UPDATE_TAG) == 0
    assert _count(neo4j_session, "DatadogApplicationKey", SECOND_UPDATE_TAG) == 0
    assert _count(neo4j_session, "DatadogAccessToken", SECOND_UPDATE_TAG) == 0


def test_failed_role_listing_keeps_graph(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    before = _snapshot(neo4j_session)
    fake_api = FakeDatadogAPI(
        paginated={**fixtures.PAGINATED_PATHS, "/api/v2/roles": []},
    )

    # Act and assert
    with pytest.raises(DatadogIncompleteListError):
        _run(neo4j_session, fake_api, SECOND_UPDATE_TAG)

    # Assert
    assert _snapshot(neo4j_session) == before
    assert _count(neo4j_session, "DatadogRole", TEST_UPDATE_TAG) == 4


def test_missing_optional_permissions_keep_key_nodes(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    fake_api = FakeDatadogAPI(
        paginated=_paginated_without("/api/v2/users", fixtures.CAROL_ID),
        failures={
            ("/api/v2/api_keys", 0): 403,
            ("/api/v2/application_keys", 0): 403,
        },
    )

    # Act
    _run(neo4j_session, fake_api, SECOND_UPDATE_TAG)

    # Assert
    snapshot = _snapshot(neo4j_session)
    # Users still sync and clean up from their complete listing.
    assert fixtures.CAROL_ID not in snapshot["DatadogUser"]
    assert _count(neo4j_session, "DatadogUser", TEST_UPDATE_TAG) == 0
    # Key and token nodes are kept, with their earlier update tag.
    assert _count(neo4j_session, "DatadogAPIKey", TEST_UPDATE_TAG) == 2
    assert _count(neo4j_session, "DatadogApplicationKey", TEST_UPDATE_TAG) == 3
    assert _count(neo4j_session, "DatadogAccessToken", TEST_UPDATE_TAG) == 2
    # Without org_app_keys_read, the access token listing isn't trusted.
    assert all(
        not url.endswith("/api/v2/personal_access_tokens")
        for _, url, _ in fake_api.requests
    )


def test_unavailable_access_tokens_keep_token_nodes(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    fake_api = FakeDatadogAPI(
        failures={("/api/v2/personal_access_tokens", 0): 404},
    )

    # Act
    _run(neo4j_session, fake_api, SECOND_UPDATE_TAG)

    # Assert
    assert _count(neo4j_session, "DatadogApplicationKey", SECOND_UPDATE_TAG) == 3
    assert _count(neo4j_session, "DatadogAccessToken", TEST_UPDATE_TAG) == 2


def test_cleanup_is_scoped_to_the_organization(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)

    # Act
    _run(neo4j_session, fixtures.other_org_api(), SECOND_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "DatadogOrganization", ["id"]) == {
        (fixtures.ORG_ID,),
        (fixtures.OTHER_ORG_ID,),
    }
    assert _count(neo4j_session, "DatadogUser", TEST_UPDATE_TAG) == (
        3 + fixtures.GENERATED_USER_COUNT
    )
    assert _count(neo4j_session, "DatadogApplicationKey", TEST_UPDATE_TAG) == 3
    assert check_rels(
        neo4j_session,
        "DatadogOrganization",
        "id",
        "DatadogUser",
        "id",
        "RESOURCE",
    ) >= {(fixtures.OTHER_ORG_ID, "user-other-0001")}
