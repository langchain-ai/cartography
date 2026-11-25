import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.datadog.util import get_object
from cartography.intel.datadog.util import relationship_id
from cartography.models.datadog.organization import DatadogOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> str:
    current_user = get(api_session, base_url)
    organization = transform(current_user, base_url)
    load_organization(
        neo4j_session,
        organization,
        common_job_parameters["UPDATE_TAG"],
    )
    return organization["id"]


@timeit
def get(api_session: requests.Session, base_url: str) -> dict[str, Any]:
    return get_object(api_session, base_url, "/api/v2/current_user")


def transform(current_user: dict[str, Any], base_url: str) -> dict[str, Any]:
    org_id = relationship_id(current_user["data"], "org")
    if not org_id:
        raise ValueError(
            "Datadog didn't return the organization of the current credential.",
        )
    attributes: dict[str, Any] = {}
    for included in current_user.get("included") or []:
        if included.get("type") == "orgs" and included.get("id") == org_id:
            attributes = included.get("attributes") or {}
    return {
        "id": org_id,
        "name": attributes.get("name"),
        "public_id": attributes.get("public_id"),
        "api_base_url": base_url,
    }


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    organization: dict[str, Any],
    update_tag: int,
) -> None:
    logger.info("Loading Datadog organization %s", organization["id"])
    load(
        neo4j_session,
        DatadogOrganizationSchema(),
        [organization],
        lastupdated=update_tag,
    )
