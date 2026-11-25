from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.baseten.util import get_json
from cartography.intel.baseten.util import team_id_for_name
from cartography.models.baseten.deployment import BasetenDeploymentSchema
from cartography.models.baseten.model import BasetenModelSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    team_ids_by_name: dict[str, str],
) -> None:
    base_url = common_job_parameters["BASE_URL"]
    models = get(api_session, base_url)
    deployments = get_deployments(
        api_session,
        base_url,
        [model["id"] for model in models],
    )
    load_models(
        neo4j_session,
        transform(models, team_ids_by_name),
        transform_deployments(deployments),
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/v1/models")["models"]


@timeit
def get_deployments(
    api_session: requests.Session,
    base_url: str,
    model_ids: list[str],
) -> list[dict[str, Any]]:
    deployments: list[dict[str, Any]] = []
    for model_id in model_ids:
        deployments.extend(
            get_json(
                api_session,
                f"{base_url}/v1/models/{model_id}/deployments",
            )["deployments"],
        )
    return deployments


def transform(
    models: list[dict[str, Any]],
    team_ids_by_name: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        {
            **model,
            "team_id": team_id_for_name(team_ids_by_name, model.get("team_name")),
        }
        for model in models
    ]


def transform_deployments(
    deployments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for deployment in deployments:
        autoscaling = deployment.get("autoscaling_settings") or {}
        region = deployment.get("region") or {}
        result.append(
            {
                "id": deployment["id"],
                "name": deployment.get("name"),
                "created_at": deployment.get("created_at"),
                "model_id": deployment["model_id"],
                "status": deployment.get("status"),
                "is_production": deployment.get("is_production"),
                "is_development": deployment.get("is_development"),
                "environment": deployment.get("environment"),
                "instance_type_name": deployment.get("instance_type_name"),
                "active_replica_count": deployment.get("active_replica_count"),
                "min_replica": autoscaling.get("min_replica"),
                "max_replica": autoscaling.get("max_replica"),
                "region": region.get("slug"),
            },
        )
    return result


@timeit
def load_models(
    neo4j_session: neo4j.Session,
    models: list[dict[str, Any]],
    deployments: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BasetenModelSchema(),
        models,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        BasetenDeploymentSchema(),
        deployments,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(BasetenDeploymentSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(BasetenModelSchema(), common_job_parameters).run(
        neo4j_session,
    )
