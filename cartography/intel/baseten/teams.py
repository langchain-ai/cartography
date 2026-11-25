from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.baseten.util import get_json
from cartography.models.baseten.team import BasetenTeamSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    teams = get(api_session, common_job_parameters["BASE_URL"])
    load_teams(
        neo4j_session,
        teams,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return teams


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/v1/teams")["teams"]


@timeit
def load_teams(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BasetenTeamSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(BasetenTeamSchema(), common_job_parameters).run(
        neo4j_session,
    )
