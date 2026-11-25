import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.datadog.util import is_permission_error
from cartography.intel.datadog.util import leak_status
from cartography.intel.datadog.util import paginated_get
from cartography.intel.datadog.util import relationship_id
from cartography.models.datadog.applicationkey import DatadogApplicationKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> bool:
    """Sync application key metadata for the whole organization.

    Return False if the credential can't list every application key.
    """
    try:
        raw_keys = get(api_session, base_url)
    except requests.HTTPError as error:
        if not is_permission_error(error):
            raise
        logger.warning(
            "Skipping Datadog application keys and access tokens: the credential "
            "lacks the org_app_keys_read permission. Existing nodes are left "
            "unchanged.",
        )
        return False
    keys = transform(raw_keys)
    load_application_keys(
        neo4j_session,
        keys,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return True


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    # The list endpoint returns partial keys without the key value. Cartography
    # never calls the single-key endpoints, which can return the value when
    # One-Time Read mode is off.
    return paginated_get(
        api_session,
        base_url,
        "/api/v2/application_keys",
        params={"sort": "created_at"},
    )


def transform(raw_keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = []
    for key in raw_keys:
        attributes = key.get("attributes") or {}
        scopes = attributes.get("scopes")
        keys.append(
            {
                "id": key["id"],
                "name": attributes.get("name"),
                "last4": attributes.get("last4"),
                "created_at": attributes.get("created_at"),
                "last_used_at": attributes.get("last_used_at"),
                "scopes": sorted(scopes) if scopes is not None else None,
                "is_scoped": bool(scopes),
                "leaked": leak_status(key),
                "owner_id": relationship_id(key, "owned_by"),
            },
        )
    return keys


@timeit
def load_application_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Datadog application keys for organization %s",
        len(data),
        org_id,
    )
    load(
        neo4j_session,
        DatadogApplicationKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        DatadogApplicationKeySchema(),
        common_job_parameters,
    ).run(neo4j_session)
