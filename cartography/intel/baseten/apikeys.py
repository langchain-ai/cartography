from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.baseten.util import get_json
from cartography.intel.baseten.util import team_id_for_name
from cartography.models.baseten.apikey import BasetenApiKeySchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    team_ids_by_name: dict[str, str],
) -> None:
    apikeys = get(api_session, common_job_parameters["BASE_URL"])
    load_apikeys(
        neo4j_session,
        transform(apikeys, team_ids_by_name),
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/v1/api_keys")["keys"]


def transform(
    apikeys: list[dict[str, Any]],
    team_ids_by_name: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for apikey in apikeys:
        owner = apikey.get("owner") or {}
        result.append(
            {
                "prefix": apikey["prefix"],
                "name": apikey.get("name"),
                "type": apikey["type"],
                "team_name": apikey.get("team_name"),
                "team_id": team_id_for_name(team_ids_by_name, apikey.get("team_name")),
                "model_ids": apikey.get("model_ids"),
                "created_at": apikey.get("created_at"),
                "expires_at": apikey.get("expires_at"),
                "last_used_at": apikey.get("last_used_at"),
                "owner_user_id": owner.get("user_id"),
                "owner_email": owner.get("email"),
            },
        )
    return result


@timeit
def load_apikeys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BasetenApiKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(BasetenApiKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
