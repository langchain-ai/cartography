import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.datadog.util import DatadogIncompleteListError
from cartography.intel.datadog.util import paginated_get
from cartography.intel.datadog.util import relationship_ids
from cartography.models.datadog.serviceaccount import DatadogServiceAccountSchema
from cartography.models.datadog.user import DatadogUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_users = get(api_session, base_url)
    users, service_accounts = transform(raw_users)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_service_accounts(
        neo4j_session,
        service_accounts,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    # Without a status filter, Datadog returns active, pending, and disabled
    # users and service accounts.
    users = paginated_get(api_session, base_url, "/api/v2/users")
    # The credential that runs the sync belongs to a user or service account,
    # so an empty listing means the read failed, not that everyone was removed.
    if not users:
        raise DatadogIncompleteListError("Datadog returned no users.")
    return users


def transform(
    raw_users: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split Datadog users into people and service accounts, keeping identity fields only."""
    users = []
    service_accounts = []
    for user in raw_users:
        attributes = user["attributes"]
        # Copy an explicit allowlist of account fields. A person is identified
        # only by the opaque Datadog ID; their email address and profile and
        # sign-in details, such as name, title, icon, MFA state, and last
        # sign-in, are never collected.
        identity = {
            "id": user["id"],
            "status": attributes.get("status"),
            "disabled": attributes.get("disabled"),
            "created_at": attributes.get("created_at"),
            "modified_at": attributes.get("modified_at"),
            "role_ids": relationship_ids(user, "roles"),
        }
        if attributes.get("service_account"):
            # A service account's name and notification address identify the
            # integration, not a person.
            identity["name"] = attributes.get("name")
            identity["email"] = attributes.get("email")
            service_accounts.append(identity)
            continue
        users.append(identity)
    return users, service_accounts


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Datadog users for organization %s", len(data), org_id)
    load(
        neo4j_session,
        DatadogUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def load_service_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Datadog service accounts for organization %s",
        len(data),
        org_id,
    )
    load(
        neo4j_session,
        DatadogServiceAccountSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DatadogUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        DatadogServiceAccountSchema(),
        common_job_parameters,
    ).run(neo4j_session)
