import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.stripe.util import is_permission_error
from cartography.intel.stripe.util import list_v2
from cartography.intel.stripe.util import sanitize_url
from cartography.models.stripe.event_destination import StripeEventDestinationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        raw_destinations = get(api_session)
    except requests.HTTPError as e:
        if not is_permission_error(e):
            raise
        logger.warning(
            "The Stripe API key can't read event destinations; skipping them. "
            "Grant the key Webhook Endpoints: Read to sync them.",
        )
        return
    load_event_destinations(
        neo4j_session,
        transform(raw_destinations),
        common_job_parameters["STRIPE_ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session) -> list[dict[str, Any]]:
    return list_v2(
        api_session,
        "/v2/core/event_destinations",
        {"include[0]": "webhook_endpoint.url"},
    )


def transform(destinations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for destination in destinations:
        webhook = destination.get("webhook_endpoint") or {}
        eventbridge = destination.get("amazon_eventbridge") or {}
        event_grid = destination.get("azure_event_grid") or {}
        disabled = (destination.get("status_details") or {}).get("disabled") or {}
        webhook_url, webhook_host = sanitize_url(webhook.get("url"))
        result.append(
            {
                "id": destination["id"],
                "name": destination.get("name"),
                "description": destination.get("description"),
                "type": destination["type"],
                "status": destination.get("status"),
                "disabled_reason": disabled.get("reason"),
                "enabled_events": destination.get("enabled_events"),
                "events_from": destination.get("events_from"),
                "event_payload": destination.get("event_payload"),
                "snapshot_api_version": destination.get("snapshot_api_version"),
                "webhook_url": webhook_url,
                "webhook_host": webhook_host,
                "aws_account_id": eventbridge.get("aws_account_id"),
                "aws_event_source_arn": eventbridge.get("aws_event_source_arn"),
                "aws_event_source_status": eventbridge.get("aws_event_source_status"),
                "azure_subscription_id": event_grid.get("azure_subscription_id"),
                "azure_resource_group_name": event_grid.get(
                    "azure_resource_group_name"
                ),
                "azure_partner_topic_name": event_grid.get("azure_partner_topic_name"),
                "azure_partner_topic_status": event_grid.get(
                    "azure_partner_topic_status"
                ),
                "azure_region": event_grid.get("azure_region"),
                "livemode": destination.get("livemode"),
                "created": destination.get("created"),
                "updated": destination.get("updated"),
            },
        )
    return result


@timeit
def load_event_destinations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        StripeEventDestinationSchema(),
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
        StripeEventDestinationSchema(),
        common_job_parameters,
    ).run(neo4j_session)
