from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class StripeWebhookEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Webhook endpoint ID, for example `we_1Mr5jULkdIwHu7ix1ibLTM0x`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        extra_index=True,
        description=(
            "URL that Stripe sends events to. Cartography drops the query string "
            "and fragment, which can carry shared secrets."
        ),
    )
    host: PropertyRef = PropertyRef(
        "host",
        extra_index=True,
        description="Host name of the endpoint URL.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Endpoint status: `enabled` or `disabled`.",
    )
    enabled_events: PropertyRef = PropertyRef(
        "enabled_events",
        description=(
            "Event types that Stripe sends to the endpoint. `*` means every "
            "event that doesn't need explicit selection."
        ),
    )
    api_version: PropertyRef = PropertyRef(
        "api_version",
        description="API version that Stripe renders the endpoint's events with.",
    )
    application: PropertyRef = PropertyRef(
        "application",
        description="ID of the Connect application that the endpoint belongs to.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Optional description of the endpoint.",
    )
    livemode: PropertyRef = PropertyRef(
        "livemode",
        description="Whether the endpoint exists in live mode.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Unix timestamp, in seconds, when the endpoint was created.",
    )


@dataclass(frozen=True)
class StripeWebhookEndpointToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
# (:StripeAccount)-[:RESOURCE]->(:StripeWebhookEndpoint)
class StripeWebhookEndpointToAccountRel(CartographyRelSchema):
    """The Stripe account has the webhook endpoint."""

    target_node_label: str = "StripeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("STRIPE_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: StripeWebhookEndpointToAccountRelProperties = (
        StripeWebhookEndpointToAccountRelProperties()
    )


@dataclass(frozen=True)
class StripeWebhookEndpointSchema(CartographyNodeSchema):
    """
    A webhook endpoint that receives Stripe events, from
    `GET /v1/webhook_endpoints`.

    Stripe returns the signing secret only when you create an endpoint, so
    Cartography never sees it.
    """

    label: str = "StripeWebhookEndpoint"
    properties: StripeWebhookEndpointNodeProperties = (
        StripeWebhookEndpointNodeProperties()
    )
    sub_resource_relationship: StripeWebhookEndpointToAccountRel = (
        StripeWebhookEndpointToAccountRel()
    )
