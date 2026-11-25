import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fireworks.util import is_access_denied
from cartography.intel.fireworks.util import paginated_get
from cartography.models.fireworks.secret import FireworksSecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    try:
        raw_secrets = get(api_session, common_job_parameters["BASE_URL"], account_id)
    except requests.HTTPError as e:
        if not is_access_denied(e):
            raise
        logger.warning(
            "Fireworks AI API key cannot list secrets in account %s; skipping secrets.",
            account_id,
        )
        return
    secrets = transform(raw_secrets)
    logger.info(
        "Loading %d Fireworks AI secrets for account %s", len(secrets), account_id
    )
    load_secrets(
        neo4j_session, secrets, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/accounts/{account_id}/secrets",
        "secrets",
    )


def transform(raw_secrets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # The API never returns `value`; only the names are copied.
    return [
        {
            "id": raw["name"],
            "key_name": raw.get("keyName"),
        }
        for raw in raw_secrets
    ]


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksSecretSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FireworksSecretSchema(), common_job_parameters).run(
        neo4j_session,
    )
