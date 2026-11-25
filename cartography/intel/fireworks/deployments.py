import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fireworks.util import paginated_get
from cartography.intel.fireworks.util import resource_id
from cartography.models.fireworks.deployment import FireworksDeploymentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    raw_deployments = get(api_session, common_job_parameters["BASE_URL"], account_id)
    deployments = transform(raw_deployments)
    logger.info(
        "Loading %d Fireworks AI deployments for account %s",
        len(deployments),
        account_id,
    )
    load_deployments(
        neo4j_session,
        deployments,
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
        api_session,
        f"{base_url}/accounts/{account_id}/deployments",
        "deployments",
    )


def transform(raw_deployments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # `directRouteApiKeys` holds credentials and is deliberately not copied.
    return [
        {
            "id": raw["name"],
            "deployment_id": resource_id(raw["name"]),
            "display_name": raw.get("displayName"),
            "description": raw.get("description"),
            "state": raw.get("state"),
            "base_model": raw.get("baseModel"),
            "accelerator_type": raw.get("acceleratorType"),
            "accelerator_count": raw.get("acceleratorCount"),
            "precision": raw.get("precision"),
            "min_replica_count": raw.get("minReplicaCount"),
            "max_replica_count": raw.get("maxReplicaCount"),
            "replica_count": raw.get("replicaCount"),
            "region": raw.get("region"),
            "direct_route_type": _direct_route_type(raw.get("directRouteType")),
            "direct_route_handle": raw.get("directRouteHandle"),
            "enable_addons": raw.get("enableAddons"),
            "preemptible": raw.get("preemptible"),
            "deployment_shape": raw.get("deploymentShape"),
            "cluster": raw.get("cluster"),
            "create_time": raw.get("createTime"),
            "update_time": raw.get("updateTime"),
        }
        for raw in raw_deployments
    ]


def _direct_route_type(value: str | None) -> str | None:
    if value in (None, "", "DIRECT_ROUTE_TYPE_UNSPECIFIED"):
        return None
    return value


@timeit
def load_deployments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksDeploymentSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FireworksDeploymentSchema(), common_job_parameters).run(
        neo4j_session,
    )
