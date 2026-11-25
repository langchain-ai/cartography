import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fireworks.util import is_access_denied
from cartography.intel.fireworks.util import paginated_get
from cartography.models.fireworks.apikey import FireworksApiKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# `-` lists the keys of every user and service account. Only admins can use it.
_ALL_USERS = "-"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    try:
        raw_keys = get(api_session, common_job_parameters["BASE_URL"], account_id)
    except requests.HTTPError as e:
        if not is_access_denied(e):
            raise
        logger.warning(
            "Fireworks AI API key cannot list every API key in account %s; use a key "
            "owned by an admin user or service account. Skipping API keys.",
            account_id,
        )
        return
    keys = transform(raw_keys)
    logger.info(
        "Loading %d Fireworks AI API keys for account %s", len(keys), account_id
    )
    load_apikeys(neo4j_session, keys, account_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/accounts/{account_id}/users/{_ALL_USERS}/apiKeys",
        "apiKeys",
    )


def transform(raw_keys: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": raw["keyId"],
            "name": raw.get("displayName"),
            "prefix": raw.get("prefix"),
            "owner_email": raw.get("email"),
            "created_at": raw.get("createTime"),
            "expires_at": raw.get("expireTime"),
            "last_used_at": raw.get("lastUsed"),
            "secure": raw.get("secure"),
            "is_firepass": raw.get("isFirepass"),
        }
        for raw in raw_keys
    ]


@timeit
def load_apikeys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksApiKeySchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FireworksApiKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
