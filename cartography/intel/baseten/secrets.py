from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.baseten.util import get_json
from cartography.models.baseten.secret import BasetenSecretSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    teams: list[dict[str, Any]],
) -> None:
    secrets = transform(
        get(api_session, common_job_parameters["BASE_URL"], teams),
    )
    load_secrets(
        neo4j_session,
        secrets,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    teams: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Read secret metadata team by team, keyed by team ID.

    `GET /v1/secrets` doesn't document which teams it covers, so each accessible
    team's secrets are read from the team-scoped endpoint instead.
    """
    return {
        team["id"]: get_json(
            api_session,
            f"{base_url}/v1/teams/{team['id']}/secrets",
        )["secrets"]
        for team in teams
    }


def transform(
    secrets_by_team_id: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    return [
        {**secret, "team_id": team_id}
        for team_id, secrets in secrets_by_team_id.items()
        for secret in secrets
    ]


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BasetenSecretSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(BasetenSecretSchema(), common_job_parameters).run(
        neo4j_session,
    )
