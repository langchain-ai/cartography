import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fireworks.util import paginated_get
from cartography.intel.fireworks.util import resource_id
from cartography.intel.fireworks.util import to_int
from cartography.models.fireworks.dataset import FireworksDatasetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    raw_datasets = get(api_session, common_job_parameters["BASE_URL"], account_id)
    datasets = transform(raw_datasets)
    logger.info(
        "Loading %d Fireworks AI datasets for account %s", len(datasets), account_id
    )
    load_datasets(
        neo4j_session, datasets, account_id, common_job_parameters["UPDATE_TAG"]
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
        f"{base_url}/accounts/{account_id}/datasets",
        "datasets",
    )


def transform(raw_datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": raw["name"],
            "dataset_id": resource_id(raw["name"]),
            "display_name": raw.get("displayName"),
            "state": raw.get("state"),
            "format": raw.get("format"),
            "example_count": to_int(raw.get("exampleCount")),
            "estimated_token_count": to_int(raw.get("estimatedTokenCount")),
            "external_url": raw.get("externalUrl"),
            "created_by": raw.get("createdBy"),
            "source_job_name": raw.get("sourceJobName"),
            "encryption_state": raw.get("encryptionState"),
            "create_time": raw.get("createTime"),
            "update_time": raw.get("updateTime"),
        }
        for raw in raw_datasets
    ]


@timeit
def load_datasets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksDatasetSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FireworksDatasetSchema(), common_job_parameters).run(
        neo4j_session,
    )
