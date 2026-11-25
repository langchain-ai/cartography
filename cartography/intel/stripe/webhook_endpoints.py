import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.stripe.util import is_permission_error
from cartography.intel.stripe.util import list_v1
from cartography.intel.stripe.util import sanitize_url
from cartography.models.stripe.webhook_endpoint import StripeWebhookEndpointSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        raw_endpoints = get(api_session)
    except requests.HTTPError as e:
        if not is_permission_error(e):
            raise
        logger.warning(
            "The Stripe API key can't read webhook endpoints; skipping them. "
            "Grant the key Webhook Endpoints: Read to sync them.",
        )
        return
    load_webhook_endpoints(
        neo4j_session,
        transform(raw_endpoints),
        common_job_parameters["STRIPE_ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session) -> list[dict[str, Any]]:
    return list_v1(api_session, "/v1/webhook_endpoints")


def transform(endpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for endpoint in endpoints:
        url, host = sanitize_url(endpoint["url"])
        result.append(
            {
                "id": endpoint["id"],
                "url": url,
                "host": host,
                "status": endpoint.get("status"),
                "enabled_events": endpoint.get("enabled_events"),
                "api_version": endpoint.get("api_version"),
                "application": endpoint.get("application"),
                "description": endpoint.get("description"),
                "livemode": endpoint.get("livemode"),
                "created": endpoint.get("created"),
            },
        )
    return result


@timeit
def load_webhook_endpoints(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        StripeWebhookEndpointSchema(),
        data,
        lastupdated=update_tag,
        STRIPE_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        StripeWebhookEndpointSchema(),
        common_job_parameters,
    ).run(neo4j_session)
