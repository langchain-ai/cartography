import json

import pytest
import requests

from cartography.config import Config
from cartography.intel.workshop import start_workshop_ingestion
from tests.data.workshop import API_KEY
from tests.data.workshop import API_URL
from tests.data.workshop import response
from tests.data.workshop import SETTINGS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@pytest.fixture(autouse=True)
def reset_workshop(neo4j_session):
    neo4j_session.run(
        "MATCH (n) WHERE n:WorkshopTenant OR n:WorkshopTag OR n:WorkshopClientMode "
        "DETACH DELETE n",
    )


def run_sync(session, tenant, update_tag):
    start_workshop_ingestion(
        session,
        Config(
            neo4j_uri="bolt://example.invalid",
            workshop_api_url=API_URL,
            workshop_api_key=API_KEY,
            workshop_tenant_id=tenant,
            update_tag=update_tag,
        ),
    )


def graph_snapshot(session):
    nodes = session.run(
        "MATCH (n) WHERE n:WorkshopTenant OR n:WorkshopTag OR n:WorkshopClientMode "
        "RETURN labels(n) AS labels, properties(n) AS properties",
    ).data()
    edges = session.run(
        "MATCH (n)-[r]->(m) WHERE n:WorkshopTenant OR n:WorkshopTag "
        "RETURN n.id AS source, m.id AS target, type(r) AS type, properties(r) AS properties",
    ).data()
    return sorted(json.dumps(record, sort_keys=True) for record in nodes + edges)


def test_sync_pagination_cleanup_and_tenant_isolation(mocker, neo4j_session):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.sync_settings.requests.get")
    get.side_effect = [response({"syncSettings": SETTINGS}), response({})] * 2

    # Act
    run_sync(neo4j_session, "tenant-a", 1)
    run_sync(neo4j_session, "tenant-b", 1)

    # Assert
    assert check_nodes(neo4j_session, "WorkshopTenant", ["id"]) == {
        ("tenant-a",),
        ("tenant-b",),
    }
    assert check_nodes(neo4j_session, "WorkshopTag", ["tenant_id", "tag"]) == {
        (tenant, item["tag"])
        for tenant in ("tenant-a", "tenant-b")
        for item in SETTINGS
    }
    assert check_rels(
        neo4j_session,
        "WorkshopTag",
        "id",
        "WorkshopClientMode",
        "id",
        "CONFIGURED_CLIENT_MODE",
    ) == {
        (
            '["' + tenant + '","' + item["tag"] + '"]',
            '["' + tenant + '","' + item["clientMode"] + '"]',
        )
        for tenant in ("tenant-a", "tenant-b")
        for item in SETTINGS
    }
    assert check_rels(
        neo4j_session,
        "WorkshopTenant",
        "id",
        "WorkshopTag",
        "tenant_id",
        "RESOURCE",
    ) == {("tenant-a", "tenant-a"), ("tenant-b", "tenant-b")}

    # Arrange
    updated = [
        {"tag": "synthetic-team", "clientMode": "LOCKDOWN"},
        {"tag": "synthetic-lab", "clientMode": "MONITOR"},
    ]
    get.side_effect = [response({"syncSettings": [item]}) for item in updated] + [
        response({})
    ]

    # Act
    run_sync(neo4j_session, "tenant-a", 2)

    # Assert
    assert check_rels(
        neo4j_session,
        "WorkshopTag",
        "id",
        "WorkshopClientMode",
        "id",
        "CONFIGURED_CLIENT_MODE",
    ) == {
        ('["tenant-a","synthetic-team"]', '["tenant-a","LOCKDOWN"]'),
        ('["tenant-a","synthetic-lab"]', '["tenant-a","MONITOR"]'),
        ('["tenant-b","synthetic-team"]', '["tenant-b","MONITOR"]'),
        ('["tenant-b","synthetic-lab"]', '["tenant-b","LOCKDOWN"]'),
    }
    assert not list(
        neo4j_session.run(
            "MATCH (t:WorkshopTag)-[:CONFIGURED_CLIENT_MODE]->(m:WorkshopClientMode) "
            "WHERE t.tenant_id <> m.tenant_id RETURN t",
        )
    )

    # Arrange
    get.side_effect = [response({"syncSettings": updated[:1]}), response({})] * 2

    # Act
    run_sync(neo4j_session, "tenant-a", 3)
    run_sync(neo4j_session, "tenant-a", 4)

    # Assert
    assert check_nodes(neo4j_session, "WorkshopTag", ["tenant_id", "tag"]) == {
        ("tenant-a", "synthetic-team"),
        ("tenant-b", "synthetic-team"),
        ("tenant-b", "synthetic-lab"),
    }
    assert check_nodes(neo4j_session, "WorkshopClientMode", ["tenant_id", "name"]) == {
        ("tenant-a", "LOCKDOWN"),
        ("tenant-b", "MONITOR"),
        ("tenant-b", "LOCKDOWN"),
    }

    # Arrange
    get.side_effect = [response({})]

    # Act
    run_sync(neo4j_session, "tenant-a", 5)

    # Assert
    assert check_nodes(neo4j_session, "WorkshopTag", ["tenant_id", "tag"]) == {
        ("tenant-b", "synthetic-team"),
        ("tenant-b", "synthetic-lab"),
    }
    assert check_nodes(neo4j_session, "WorkshopClientMode", ["tenant_id", "name"]) == {
        ("tenant-b", "MONITOR"),
        ("tenant-b", "LOCKDOWN"),
    }


@pytest.mark.parametrize(
    "failure",
    [
        response({}, 403),
        response({}, 500),
        requests.Timeout(),
        response({"syncSettings": None}),
        response({"syncSettings": [{"tag": "synthetic-bad", "clientMode": "INVALID"}]}),
        response({"syncSettings": SETTINGS}),
        response({"syncSettings": [], "nextPageToken": "synthetic"}),
    ],
)
@pytest.mark.parametrize("after_page", [False, True])
def test_incomplete_reads_preserve_graph(mocker, neo4j_session, failure, after_page):
    # Arrange
    get = mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get",
        side_effect=[response({"syncSettings": SETTINGS}), response({})],
    )
    run_sync(neo4j_session, "tenant-a", 1)
    before = graph_snapshot(neo4j_session)
    pages = [response({"syncSettings": SETTINGS})] if after_page else []
    if (
        not after_page
        and isinstance(failure, requests.Response)
        and failure.json() == {"syncSettings": SETTINGS}
    ):
        pages.append(failure)
    get.side_effect = pages + [failure]

    # Act and assert
    with pytest.raises((ValueError, requests.RequestException)):
        run_sync(neo4j_session, "tenant-a", 2)
    assert graph_snapshot(neo4j_session) == before


def test_unknown_mode_is_not_inferred(mocker, neo4j_session):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.sync_settings.requests.get",
        side_effect=[response({"syncSettings": [{"tag": "global"}]}), response({})],
    )

    # Act
    run_sync(neo4j_session, "tenant-a", 1)

    # Assert
    assert check_rels(
        neo4j_session,
        "WorkshopTag",
        "tag",
        "WorkshopClientMode",
        "name",
        "CONFIGURED_CLIENT_MODE",
    ) == {("global", "UNKNOWN_CLIENT_MODE")}
