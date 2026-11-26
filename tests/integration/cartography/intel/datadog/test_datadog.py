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
]

USER_PROPERTIES = {
    "id",
    "email",
    "status",
    "disabled",
    "created_at",
    "modified_at",
    "lastupdated",
    "firstseen",
}


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


def _snapshot(neo4j_session) -> dict[str, set]:
    snapshot: dict[str, set] = {
        label: {
            record["id"]
            for record in neo4j_session.run(f"MATCH (n:{label}) RETURN n.id AS id")
        }
        for label in DATADOG_LABELS
    }
    snapshot["HAS_ROLE"] = {
        (record["a"], record["r"])
        for record in neo4j_session.run(
            "MATCH (a)-[:HAS_ROLE]->(r:DatadogRole) RETURN a.id AS a, r.id AS r",
        )
    }
    return snapshot


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
        (fixtures.AUDITOR_ROLE_ID, "Access auditor"),
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
            ["id", "email", "status", "disabled"],
        )
        if not row[0].startswith("user-gen-")
    }
    assert named_users == {
        (fixtures.ALICE_ID, "alice@example.com", "Active", False),
        (fixtures.BOB_ID, "bob@example.com", "Disabled", True),
        (fixtures.CAROL_ID, "carol@example.com", "Pending", False),
    }
    assert check_nodes(
        neo4j_session,
        "DatadogServiceAccount",
        ["id", "name", "email", "disabled"],
    ) == {
        (fixtures.CI_SA_ID, "ci-deployer", "ci-deployer@example.com", False),
        (
            fixtures.CARTOGRAPHY_SA_ID,
            "cartography-readonly",
            "security@example.com",
            False,
        ),
    }
    assert (
        _count(neo4j_session, "DatadogUser:UserAccount")
        == 3 + fixtures.GENERATED_USER_COUNT
    )
    assert _count(neo4j_session, "DatadogServiceAccount:ServiceAccount") == 2
    assert _count(neo4j_session, "DatadogRole:PermissionRole") == 4

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
    generated_memberships = neo4j_session.run(
        """
        MATCH (u:DatadogUser)-[:HAS_ROLE]->(:DatadogRole {id: $role})
        WHERE u.id STARTS WITH 'user-gen-'
        RETURN count(u) AS c
        """,
        role=fixtures.READ_ONLY_ROLE_ID,
    ).single()["c"]
    assert generated_memberships == fixtures.GENERATED_USER_COUNT
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

    resource_targets = neo4j_session.run(
        """
        MATCH (:DatadogOrganization {id: $org})-[:RESOURCE]->(n)
        RETURN count(n) AS c
        """,
        org=fixtures.ORG_ID,
    ).single()["c"]
    assert resource_targets == 4 + 3 + fixtures.GENERATED_USER_COUNT + 2

    # The module sends only GET requests, and only to the four
    # access-governance endpoints.
    assert {method for method, _, _ in fake_api.requests} == {"GET"}
    assert {url for _, url, _ in fake_api.requests} == {
        f"{FakeDatadogAPI.base_url}/api/v2/current_user",
        f"{FakeDatadogAPI.base_url}/api/v2/roles",
        f"{FakeDatadogAPI.base_url}/api/v2/permissions",
        f"{FakeDatadogAPI.base_url}/api/v2/users",
    }


def test_sync_datadog_stores_no_profile_details(neo4j_session):
    # Arrange
    _reset(neo4j_session)

    # Act
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)

    # Assert
    for record in neo4j_session.run(
        "MATCH (u:DatadogUser) RETURN properties(u) AS props",
    ):
        props = record["props"]
        assert {key for key in props if not key.startswith("_")} <= USER_PROPERTIES
        assert not set(fixtures.PROFILE_ATTRIBUTES) & set(props)
        for value in props.values():
            assert str(value) not in fixtures.PROFILE_SENTINELS


def test_complete_resync_removes_stale_nodes(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    paginated = _paginated_without("/api/v2/users", fixtures.BOB_ID)
    paginated["/api/v2/roles"] = [
        role
        for role in paginated["/api/v2/roles"]
        if role["id"] != fixtures.AUDITOR_ROLE_ID
    ]
    for user in paginated["/api/v2/users"]:
        if user["id"] == fixtures.ALICE_ID:
            user["relationships"]["roles"]["data"] = [
                {"type": "roles", "id": fixtures.READ_ONLY_ROLE_ID},
            ]
        if user["id"] == fixtures.CARTOGRAPHY_SA_ID:
            user["relationships"]["roles"]["data"] = [
                {"type": "roles", "id": fixtures.READ_ONLY_ROLE_ID},
            ]

    # Act
    _run(neo4j_session, FakeDatadogAPI(paginated=paginated), SECOND_UPDATE_TAG)

    # Assert
    snapshot = _snapshot(neo4j_session)
    assert fixtures.BOB_ID not in snapshot["DatadogUser"]
    assert fixtures.ALICE_ID in snapshot["DatadogUser"]
    assert fixtures.AUDITOR_ROLE_ID not in snapshot["DatadogRole"]
    assert (fixtures.ALICE_ID, fixtures.ADMIN_ROLE_ID) not in snapshot["HAS_ROLE"]
    assert (fixtures.ALICE_ID, fixtures.READ_ONLY_ROLE_ID) in snapshot["HAS_ROLE"]
    assert (fixtures.CARTOGRAPHY_SA_ID, fixtures.READ_ONLY_ROLE_ID) in snapshot[
        "HAS_ROLE"
    ]
    assert _count(neo4j_session, "DatadogUser", TEST_UPDATE_TAG) == 0
    assert _count(neo4j_session, "DatadogRole", TEST_UPDATE_TAG) == 0


@pytest.mark.parametrize(
    "fake_api",
    [
        pytest.param(
            FakeDatadogAPI(
                paginated=_paginated_without("/api/v2/users", fixtures.BOB_ID),
                failures={("/api/v2/users", 0): 403},
            ),
            id="users-denied",
        ),
        pytest.param(
            FakeDatadogAPI(
                paginated=_paginated_without("/api/v2/users", fixtures.BOB_ID),
                failures={("/api/v2/users", 1): 403},
            ),
            id="users-denied-mid-listing",
        ),
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
def test_denied_failed_or_partial_user_listing_keeps_graph(neo4j_session, fake_api):
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
    assert _count(neo4j_session, "DatadogUser", SECOND_UPDATE_TAG) == 0
    assert _count(neo4j_session, "DatadogServiceAccount", SECOND_UPDATE_TAG) == 0


@pytest.mark.parametrize(
    "fake_api",
    [
        pytest.param(
            FakeDatadogAPI(
                paginated={**fixtures.PAGINATED_PATHS, "/api/v2/roles": []},
            ),
            id="empty-role-listing",
        ),
        pytest.param(
            FakeDatadogAPI(failures={("/api/v2/roles", 0): 403}),
            id="roles-denied",
        ),
        pytest.param(
            FakeDatadogAPI(failures={("/api/v2/permissions", 0): 403}),
            id="permissions-denied",
        ),
        pytest.param(
            FakeDatadogAPI(failures={("/api/v2/current_user", 0): 401}),
            id="credential-rejected",
        ),
    ],
)
def test_denied_or_empty_role_reads_keep_graph(neo4j_session, fake_api):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    before = _snapshot(neo4j_session)

    # Act and assert
    with pytest.raises((requests.HTTPError, DatadogIncompleteListError)):
        _run(neo4j_session, fake_api, SECOND_UPDATE_TAG)

    # Assert
    assert _snapshot(neo4j_session) == before
    assert _count(neo4j_session, "DatadogRole", TEST_UPDATE_TAG) == 4
    assert _count(neo4j_session, "DatadogUser", TEST_UPDATE_TAG) == (
        3 + fixtures.GENERATED_USER_COUNT
    )


def test_cleanup_is_scoped_to_the_organization(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _run(neo4j_session, FakeDatadogAPI(), TEST_UPDATE_TAG)
    before = _snapshot(neo4j_session)

    # Act
    _run(neo4j_session, fixtures.other_org_api(), SECOND_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "DatadogOrganization", ["id"]) == {
        (fixtures.ORG_ID,),
        (fixtures.OTHER_ORG_ID,),
    }
    after = _snapshot(neo4j_session)
    assert before["DatadogUser"] <= after["DatadogUser"]
    assert before["DatadogRole"] <= after["DatadogRole"]
    assert before["HAS_ROLE"] <= after["HAS_ROLE"]
    assert _count(neo4j_session, "DatadogUser", TEST_UPDATE_TAG) == (
        3 + fixtures.GENERATED_USER_COUNT
    )
    assert check_rels(
        neo4j_session,
        "DatadogOrganization",
        "id",
        "DatadogUser",
        "id",
        "RESOURCE",
    ) >= {(fixtures.OTHER_ORG_ID, "user-other-0001")}
    other_org_users = neo4j_session.run(
        """
        MATCH (:DatadogOrganization {id: $org})-[:RESOURCE]->(u:DatadogUser)
        RETURN count(u) AS c
        """,
        org=fixtures.OTHER_ORG_ID,
    ).single()["c"]
    assert other_org_users == 1
