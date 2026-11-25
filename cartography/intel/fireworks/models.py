import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fireworks.util import paginated_get
from cartography.intel.fireworks.util import resource_id
from cartography.models.fireworks.model import FireworksModelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    raw_models = get(api_session, common_job_parameters["BASE_URL"], account_id)
    models = transform(raw_models)
    logger.info(
        "Loading %d Fireworks AI models for account %s", len(models), account_id
    )
    load_models(neo4j_session, models, account_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/accounts/{account_id}/models",
        "models",
    )


def transform(raw_models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": raw["name"],
            "model_id": resource_id(raw["name"]),
            "display_name": raw.get("displayName"),
            "description": raw.get("description"),
            "kind": raw.get("kind"),
            "state": raw.get("state"),
            "public": raw.get("public"),
            "base_model": (raw.get("peftDetails") or {}).get("baseModel"),
            "imported_from": raw.get("importedFrom"),
            "fine_tuning_job": raw.get("fineTuningJob"),
            "hugging_face_url": raw.get("huggingFaceUrl"),
            "github_url": raw.get("githubUrl"),
            "encryption_state": raw.get("encryptionState"),
            "cluster": raw.get("cluster"),
            "context_length": raw.get("contextLength"),
            "supports_tools": raw.get("supportsTools"),
            "supports_image_input": raw.get("supportsImageInput"),
            "create_time": raw.get("createTime"),
            "update_time": raw.get("updateTime"),
        }
        for raw in raw_models
    ]


@timeit
def load_models(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksModelSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FireworksModelSchema(), common_job_parameters).run(
        neo4j_session,
    )
