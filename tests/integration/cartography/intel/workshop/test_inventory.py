import json

import pytest
import requests

from cartography.config import Config
from cartography.intel.workshop import start_workshop_ingestion
from tests.data.workshop import API_KEY
from tests.data.workshop import API_URL
from tests.data.workshop import HOSTS
from tests.data.workshop import response
from tests.data.workshop import SETTINGS
from tests.data.workshop import TAGS
from tests.data.workshop import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

LABELS = [
    "WorkshopTenant",
    "WorkshopTag",
    "WorkshopClientMode",
    "WorkshopHost",
    "WorkshopUser",
]


@pytest.fixture(autouse=True)
def reset_workshop(neo4j_session):
    neo4j_session.run(
        "MATCH (n) WHERE any(label IN labels(n) WHERE label IN $labels) DETACH DELETE n",
        labels=LABELS,
    )


def read(method, data):
    field = {
        "ListSyncSettings": "syncSettings",
        "ListHosts": "hosts",
        "ListUsers": "users",
        "ListTags": "tags",
    }[method]
    return [response({field: data}), response({})] if data else [response({})]


def full_read(settings=SETTINGS, hosts=HOSTS, users=USERS, tags=TAGS):
    return (
        read("ListSyncSettings", settings)
        + read("ListHosts", hosts)
        + read("ListUsers", users)
        + read("ListTags", tags)
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


def snapshot(session):
    nodes = session.run(
        "MATCH (n) WHERE any(label IN labels(n) WHERE label IN $labels) RETURN labels(n) AS labels, properties(n) AS properties",
        labels=LABELS,
    ).data()
    edges = session.run(
        "MATCH (n)-[r]->(m) WHERE any(label IN labels(n) WHERE label IN $labels) RETURN n.id AS source, type(r) AS type, m.id AS target, properties(r) AS properties",
        labels=LABELS,
    ).data()
    return sorted(json.dumps(record, sort_keys=True) for record in nodes + edges)


def test_inventory_links_hosts_tags_and_users(mocker, neo4j_session):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.sync_settings.requests.get")
    mocker.patch("cartography.intel.workshop.inventory.requests.get", new=get)
    get.side_effect = full_read() * 2

    # Act
    run_sync(neo4j_session, "tenant-a", 1)
    run_sync(neo4j_session, "tenant-b", 1)

    # Assert
    assert check_nodes(
        neo4j_session, "WorkshopHost", ["tenant_id", "hostname", "primary_user"]
    ) == {
        (tenant, "synthetic-workstation", "synthetic-user@example.invalid")
        for tenant in ("tenant-a", "tenant-b")
    }
    assert check_nodes(
        neo4j_session, "WorkshopUser", ["tenant_id", "username", "department_name"]
    ) == {
        (tenant, "synthetic-user@example.invalid", "Synthetic Department")
        for tenant in ("tenant-a", "tenant-b")
    }
    assert check_rels(
        neo4j_session, "WorkshopHost", "id", "WorkshopTag", "id", "HAS_TAG"
    ) == {
        (f'["{tenant}","synthetic-host-1"]', f'["{tenant}","{tag}"]')
        for tenant in ("tenant-a", "tenant-b")
        for tag in ("synthetic-team", "synthetic-inventory-only")
    }
    assert check_rels(
        neo4j_session, "WorkshopHost", "id", "WorkshopUser", "id", "PRIMARY_USER"
    ) == {
        (f'["{tenant}","synthetic-host-1"]', f'["{tenant}","synthetic-user-1"]')
        for tenant in ("tenant-a", "tenant-b")
    }
    assert check_nodes(neo4j_session, "WorkshopTag", ["tenant_id", "tag"]) >= {
        ("tenant-a", "synthetic-catalog-only"),
        ("tenant-a", "synthetic-inventory-only"),
    }
    assert not neo4j_session.run(
        "MATCH (:WorkshopHost)-[r]->(m:WorkshopClientMode) RETURN r"
    ).data()

    # Arrange
    get.side_effect = full_read(
        hosts=[
            {
                **HOSTS[0],
                "tags": ["synthetic-team"],
                "primaryUser": "unmatched@example.invalid",
            }
        ],
        tags=[{"tag": "synthetic-inventory-only"}],
    )

    # Act
    run_sync(neo4j_session, "tenant-a", 2)

    # Assert
    assert check_rels(
        neo4j_session, "WorkshopHost", "id", "WorkshopTag", "id", "HAS_TAG"
    ) == {
        ('["tenant-a","synthetic-host-1"]', '["tenant-a","synthetic-team"]'),
        ('["tenant-b","synthetic-host-1"]', '["tenant-b","synthetic-team"]'),
        ('["tenant-b","synthetic-host-1"]', '["tenant-b","synthetic-inventory-only"]'),
    }
    assert check_rels(
        neo4j_session, "WorkshopHost", "id", "WorkshopUser", "id", "PRIMARY_USER"
    ) == {
        ('["tenant-b","synthetic-host-1"]', '["tenant-b","synthetic-user-1"]'),
    }
    assert ("tenant-a", "synthetic-catalog-only") not in check_nodes(
        neo4j_session, "WorkshopTag", ["tenant_id", "tag"]
    )

    # Arrange
    get.side_effect = full_read(settings=[], hosts=[], users=[], tags=[])

    # Act
    run_sync(neo4j_session, "tenant-a", 3)

    # Assert
    assert check_nodes(neo4j_session, "WorkshopHost", ["tenant_id"]) == {("tenant-b",)}
    assert check_nodes(neo4j_session, "WorkshopUser", ["tenant_id"]) == {("tenant-b",)}
    assert check_nodes(neo4j_session, "WorkshopTag", ["tenant_id"]) == {("tenant-b",)}


@pytest.mark.parametrize("failure_index", [1, 2, 4, 6, 7])
@pytest.mark.parametrize(
    "failure", [response({}, 403), requests.Timeout(), response({"hosts": None})]
)
def test_any_incomplete_inventory_read_preserves_graph(
    mocker, neo4j_session, failure_index, failure
):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.sync_settings.requests.get")
    mocker.patch("cartography.intel.workshop.inventory.requests.get", new=get)
    get.side_effect = full_read()
    run_sync(neo4j_session, "tenant-a", 1)
    before = snapshot(neo4j_session)
    reads = full_read(hosts=[{**HOSTS[0], "hostname": "changed"}])
    reads[failure_index] = failure
    get.side_effect = reads

    # Act and assert
    with pytest.raises((ValueError, requests.RequestException)):
        run_sync(neo4j_session, "tenant-a", 2)
    assert snapshot(neo4j_session) == before


def test_truncated_host_tags_preserve_graph(mocker, neo4j_session):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.sync_settings.requests.get")
    mocker.patch("cartography.intel.workshop.inventory.requests.get", new=get)
    get.side_effect = full_read()
    run_sync(neo4j_session, "tenant-a", 1)
    before = snapshot(neo4j_session)
    get.side_effect = full_read(hosts=[{**HOSTS[0], "tagsTruncated": True}])

    # Act and assert
    with pytest.raises(ValueError):
        run_sync(neo4j_session, "tenant-a", 2)
    assert snapshot(neo4j_session) == before


def test_idempotency_and_removed_settings_or_directory_records(mocker, neo4j_session):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.sync_settings.requests.get")
    mocker.patch("cartography.intel.workshop.inventory.requests.get", new=get)
    get.side_effect = full_read() * 2
    run_sync(neo4j_session, "tenant-a", 1)
    before = snapshot(neo4j_session)

    # Act
    run_sync(neo4j_session, "tenant-a", 1)

    # Assert
    assert snapshot(neo4j_session) == before

    # Arrange
    get.side_effect = full_read(settings=[], users=[])

    # Act
    run_sync(neo4j_session, "tenant-a", 2)

    # Assert
    assert check_nodes(neo4j_session, "WorkshopHost", ["primary_user"]) == {
        ("synthetic-user@example.invalid",),
    }
    assert not check_nodes(neo4j_session, "WorkshopUser", ["id"])
    assert not check_nodes(neo4j_session, "WorkshopClientMode", ["id"])
    assert not check_rels(
        neo4j_session, "WorkshopHost", "id", "WorkshopUser", "id", "PRIMARY_USER"
    )
    assert check_rels(
        neo4j_session, "WorkshopHost", "uuid", "WorkshopTag", "tag", "HAS_TAG"
    ) == {
        ("synthetic-host-1", "synthetic-team"),
        ("synthetic-host-1", "synthetic-inventory-only"),
    }
