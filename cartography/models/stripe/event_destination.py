from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class StripeEventDestinationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Event destination ID, for example `ed_61RM8ltWcTW4mbsxf16RJyfa2xSQ`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="User-defined name of the destination.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Optional description of the destination.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Delivery transport: `webhook_endpoint`, `amazon_eventbridge`, or "
            "`azure_event_grid`."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Destination status: `enabled` or `disabled`.",
    )
    disabled_reason: PropertyRef = PropertyRef(
        "disabled_reason",
        description=(
            "Why the destination is disabled, such as `user` or "
            "`no_aws_event_source_exists`."
        ),
    )
    enabled_events: PropertyRef = PropertyRef(
        "enabled_events",
        description="Event types that Stripe delivers to the destination.",
    )
    events_from: PropertyRef = PropertyRef(
        "events_from",
        description=(
            "Accounts whose events the destination receives: `@self`, "
            "`@accounts` for connected accounts, `@organization_members`, or "
            "`@organization_members/@accounts`."
        ),
    )
    event_payload: PropertyRef = PropertyRef(
        "event_payload",
        description=(
            "`snapshot` events carry a copy of the changed object. `thin` events "
            "carry only its ID."
        ),
    )
    snapshot_api_version: PropertyRef = PropertyRef(
        "snapshot_api_version",
        description="API version that Stripe renders snapshot events with.",
    )
    webhook_url: PropertyRef = PropertyRef(
        "webhook_url",
        extra_index=True,
        description=(
            "`webhook_endpoint` destinations only. URL that Stripe sends events "
            "to, without its query string and fragment."
        ),
    )
    webhook_host: PropertyRef = PropertyRef(
        "webhook_host",
        description="`webhook_endpoint` destinations only. Host name of the URL.",
    )
    aws_account_id: PropertyRef = PropertyRef(
        "aws_account_id",
        extra_index=True,
        description=(
            "`amazon_eventbridge` destinations only. AWS account that owns the "
            "event bus that receives the events."
        ),
    )
    aws_event_source_arn: PropertyRef = PropertyRef(
        "aws_event_source_arn",
        description=(
            "`amazon_eventbridge` destinations only. ARN of the partner event "
            "source that Stripe created in the AWS account."
        ),
    )
    aws_event_source_status: PropertyRef = PropertyRef(
        "aws_event_source_status",
        description=(
            "`amazon_eventbridge` destinations only. State of the partner event "
            "source: `active`, `pending`, `deleted`, or `unknown`."
        ),
    )
    azure_subscription_id: PropertyRef = PropertyRef(
        "azure_subscription_id",
        extra_index=True,
        description=(
            "`azure_event_grid` destinations only. Azure subscription that "
            "contains the partner topic."
        ),
    )
    azure_resource_group_name: PropertyRef = PropertyRef(
        "azure_resource_group_name",
        description=(
            "`azure_event_grid` destinations only. Resource group that contains "
            "the partner topic."
        ),
    )
    azure_partner_topic_name: PropertyRef = PropertyRef(
        "azure_partner_topic_name",
        description=(
            "`azure_event_grid` destinations only. Name of the partner topic "
            "that Stripe created."
        ),
    )
    azure_partner_topic_status: PropertyRef = PropertyRef(
        "azure_partner_topic_status",
        description=(
            "`azure_event_grid` destinations only. State of the partner topic, "
            "such as `activated` or `never_activated`."
        ),
    )
    azure_region: PropertyRef = PropertyRef(
        "azure_region",
        description="`azure_event_grid` destinations only. Region of the partner topic.",
    )
    livemode: PropertyRef = PropertyRef(
        "livemode",
        description="Whether the destination exists in live mode.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Time when the destination was created.",
    )
    updated: PropertyRef = PropertyRef(
        "updated",
        description="Time when the destination was last updated.",
    )


@dataclass(frozen=True)
class StripeEventDestinationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
# (:StripeAccount)-[:RESOURCE]->(:StripeEventDestination)
class StripeEventDestinationToAccountRel(CartographyRelSchema):
    """The Stripe account has the event destination."""

    target_node_label: str = "StripeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("STRIPE_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: StripeEventDestinationToAccountRelProperties = (
        StripeEventDestinationToAccountRelProperties()
    )


@dataclass(frozen=True)
class StripeEventDestinationToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
# (:StripeEventDestination)-[:DELIVERS_TO]->(:AWSAccount)
class StripeEventDestinationToAWSAccountRel(CartographyRelSchema):
    """
    An `amazon_eventbridge` destination delivers Stripe events to the AWS
    account. Only created when the AWS account is already in the graph.
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DELIVERS_TO"
    properties: StripeEventDestinationToAWSAccountRelProperties = (
        StripeEventDestinationToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class StripeEventDestinationToAzureSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
# (:StripeEventDestination)-[:DELIVERS_TO]->(:AzureSubscription)
class StripeEventDestinationToAzureSubscriptionRel(CartographyRelSchema):
    """
    An `azure_event_grid` destination delivers Stripe events to the Azure
    subscription. Only created when the subscription is already in the graph.
    """

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("azure_subscription_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DELIVERS_TO"
    properties: StripeEventDestinationToAzureSubscriptionRelProperties = (
        StripeEventDestinationToAzureSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class StripeEventDestinationSchema(CartographyNodeSchema):
    """
    An event destination that receives Stripe events through a webhook,
    Amazon EventBridge, or Azure Event Grid, from
    `GET /v2/core/event_destinations`.

    Webhook endpoints that you create through the v1 API also appear as
    `StripeWebhookEndpoint` nodes. Stripe doesn't document whether the two
    lists overlap, so the same endpoint can appear under both labels.
    """

    label: str = "StripeEventDestination"
    properties: StripeEventDestinationNodeProperties = (
        StripeEventDestinationNodeProperties()
    )
    sub_resource_relationship: StripeEventDestinationToAccountRel = (
        StripeEventDestinationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            StripeEventDestinationToAWSAccountRel(),
            StripeEventDestinationToAzureSubscriptionRel(),
        ],
    )
