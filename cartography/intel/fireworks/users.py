import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fireworks.util import paginated_get
from cartography.intel.fireworks.util import resource_id
from cartography.models.fireworks.serviceaccount import FireworksServiceAccountSchema
from cartography.models.fireworks.user import FireworksUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    raw_users = get(api_session, common_job_parameters["BASE_URL"], account_id)
    users, service_accounts = transform(raw_users)
    logger.info(
        "Loading %d Fireworks AI users and %d service accounts for account %s",
        len(users),
        len(service_accounts),
        account_id,
    )
    load_users(
        neo4j_session,
        users,
        service_accounts,
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session, f"{base_url}/accounts/{account_id}/users", "users"
    )


def transform(
    raw_users: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    users: list[dict[str, Any]] = []
    service_accounts: list[dict[str, Any]] = []
    for raw in raw_users:
        user = {
            "id": raw["name"],
            "user_id": resource_id(raw["name"]),
            "display_name": raw.get("displayName"),
            "email": raw.get("email"),
            "role": raw.get("role"),
            "permission_preset": raw.get("permissionPreset"),
            "state": raw.get("state"),
            "create_time": raw.get("createTime"),
            "update_time": raw.get("updateTime"),
        }
        if raw.get("serviceAccount"):
            service_accounts.append(user)
        else:
            users.append(user)
    return users, service_accounts


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    service_accounts: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksUserSchema(),
        users,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        FireworksServiceAccountSchema(),
        service_accounts,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FireworksUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        FireworksServiceAccountSchema(),
        common_job_parameters,
    ).run(neo4j_session)
