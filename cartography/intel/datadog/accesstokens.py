import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.datadog.util import is_permission_error
from cartography.intel.datadog.util import leak_status
from cartography.intel.datadog.util import paginated_get
from cartography.intel.datadog.util import relationship_id
from cartography.models.datadog.accesstoken import DatadogAccessTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

TOKEN_TYPES = {
    "personal_access_tokens": "personal",
    "service_access_tokens": "service",
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> bool:
    """Sync personal and service access token metadata.

    Call this only after the organization-wide application key listing
    succeeded. The token listing also accepts the `user_app_keys` permission,
    which may return only the caller's own tokens, and a sync must never clean
    up from such a partial listing. Return False if the listing isn't
    available to the credential.
    """
    try:
        raw_tokens = get(api_session, base_url)
    except requests.HTTPError as error:
        # 404 covers organizations where access tokens aren't available yet.
        if not (
            is_permission_error(error)
            or (error.response is not None and error.response.status_code == 404)
        ):
            raise
        logger.warning(
            "Skipping Datadog access tokens: the listing isn't available to this "
            "credential. Existing DatadogAccessToken nodes are left unchanged.",
        )
        return False
    tokens = transform(raw_tokens)
    load_access_tokens(
        neo4j_session,
        tokens,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return True


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    # The list endpoint returns token metadata without the token secret.
    return paginated_get(
        api_session,
        base_url,
        "/api/v2/personal_access_tokens",
        params={"sort": "created_at"},
    )


def transform(raw_tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tokens = []
    for token in raw_tokens:
        attributes = token.get("attributes") or {}
        scopes = attributes.get("scopes")
        tokens.append(
            {
                "id": token["id"],
                "name": attributes.get("name"),
                "token_type": TOKEN_TYPES.get(token.get("type") or ""),
                "created_at": attributes.get("created_at"),
                "modified_at": attributes.get("modified_at"),
                "expires_at": attributes.get("expires_at"),
                "last_used_at": attributes.get("last_used_at"),
                "scopes": sorted(scopes) if scopes is not None else None,
                "leaked": leak_status(token),
                "owner_id": relationship_id(token, "owned_by"),
            },
        )
    return tokens


@timeit
def load_access_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Datadog access tokens for organization %s",
        len(data),
        org_id,
    )
    load(
        neo4j_session,
        DatadogAccessTokenSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DatadogAccessTokenSchema(), common_job_parameters).run(
        neo4j_session,
    )
