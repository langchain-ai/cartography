from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.baseten.util import paginated_get
from cartography.models.baseten.environment_group import BasetenEnvironmentGroupSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    teams: list[dict[str, Any]],
) -> None:
    groups = get(
        api_session,
        common_job_parameters["BASE_URL"],
        [team["id"] for team in teams],
    )
    load_environment_groups(
        neo4j_session,
        transform(groups),
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_ids: list[str],
) -> list[dict[str, Any]]:
    """Read every accessible team's environment groups.

    The top-level `GET /v1/environment_groups` only covers the default team, so each
    team is read from its team-scoped endpoint.
    """
    groups: list[dict[str, Any]] = []
    for team_id in team_ids:
        groups.extend(
            paginated_get(
                api_session,
                f"{base_url}/v1/teams/{team_id}/environment_groups",
            ),
        )
    return groups


def transform(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for group in groups:
        manage_access = group.get("manage_access") or {}
        result.append(
            {
                "id": f"{group['team_id']}/{group['name']}",
                "name": group["name"],
                "team_id": group["team_id"],
                "team_name": group.get("team_name"),
                "is_restricted": manage_access.get("is_restricted"),
                "manager_user_ids": [
                    user["user_id"] for user in manage_access.get("users") or []
                ],
            },
        )
    return result


@timeit
def load_environment_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BasetenEnvironmentGroupSchema(),
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
        BasetenEnvironmentGroupSchema(),
        common_job_parameters,
    ).run(neo4j_session)
