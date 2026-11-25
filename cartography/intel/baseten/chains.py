from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.baseten.util import get_json
from cartography.intel.baseten.util import team_id_for_name
from cartography.models.baseten.chain import BasetenChainSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    team_ids_by_name: dict[str, str],
) -> None:
    chains = get(api_session, common_job_parameters["BASE_URL"])
    load_chains(
        neo4j_session,
        transform(chains, team_ids_by_name),
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/v1/chains")["chains"]


def transform(
    chains: list[dict[str, Any]],
    team_ids_by_name: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        {
            **chain,
            "team_id": team_id_for_name(team_ids_by_name, chain.get("team_name")),
        }
        for chain in chains
    ]


@timeit
def load_chains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BasetenChainSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(BasetenChainSchema(), common_job_parameters).run(
        neo4j_session,
    )
