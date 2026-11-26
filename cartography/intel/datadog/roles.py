import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.datadog.util import DatadogIncompleteListError
from cartography.intel.datadog.util import get_object
from cartography.intel.datadog.util import paginated_get
from cartography.intel.datadog.util import relationship_ids
from cartography.models.datadog.role import DatadogRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_roles = get(api_session, base_url)
    raw_permissions = get_permissions(api_session, base_url)
    roles = transform(raw_roles, raw_permissions)
    load_roles(
        neo4j_session,
        roles,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    roles = paginated_get(api_session, base_url, "/api/v2/roles")
    # Every organization has the managed Admin, Standard, and Read Only roles,
    # so an empty listing means the read failed, not that roles were deleted.
    if not roles:
        raise DatadogIncompleteListError("Datadog returned no roles.")
    return roles


@timeit
def get_permissions(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return get_object(api_session, base_url, "/api/v2/permissions")["data"]


def transform(
    raw_roles: list[dict[str, Any]],
    raw_permissions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    permission_names = {
        permission["id"]: permission["attributes"]["name"]
        for permission in raw_permissions
    }
    roles = []
    for role in raw_roles:
        attributes = role.get("attributes") or {}
        permission_ids = relationship_ids(role, "permissions")
        unknown = [pid for pid in permission_ids if pid not in permission_names]
        if unknown:
            logger.warning(
                "Datadog role %s grants %d permissions missing from /api/v2/permissions; "
                "keeping their IDs.",
                role["id"],
                len(unknown),
            )
        roles.append(
            {
                "id": role["id"],
                "name": attributes.get("name"),
                "created_at": attributes.get("created_at"),
                "modified_at": attributes.get("modified_at"),
                "user_count": attributes.get("user_count"),
                "receives_permissions_from": attributes.get(
                    "receives_permissions_from",
                ),
                "permissions": sorted(
                    {permission_names.get(pid, pid) for pid in permission_ids},
                ),
            },
        )
    return roles


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Datadog roles for organization %s", len(data), org_id)
    load(
        neo4j_session,
        DatadogRoleSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DatadogRoleSchema(), common_job_parameters).run(
        neo4j_session,
    )
