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
class StripeConnectedAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stripe account ID of the connected account.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Customer-facing business name of the connected account.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Name that the Stripe Dashboard shows for the connected account.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        description="Business website from the connected account's business profile.",
    )
    mcc: PropertyRef = PropertyRef(
        "mcc",
        description="Merchant category code of the connected account.",
    )
    country: PropertyRef = PropertyRef(
        "country",
        description="Two-letter country code of the connected account.",
    )
    default_currency: PropertyRef = PropertyRef(
        "default_currency",
        description="Three-letter ISO code of the connected account's default currency.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Legacy account type: `standard`, `express`, `custom`, or `none`.",
    )
    business_type: PropertyRef = PropertyRef(
        "business_type",
        description=(
            "Business type, such as `company`, `individual`, `non_profit`, or "
            "`government_entity`."
        ),
    )
    controller_type: PropertyRef = PropertyRef(
        "controller_type",
        description=(
            "`application` when a Connect platform controls the account, or "
            "`account` when it controls itself."
        ),
    )
    controller_is_controller: PropertyRef = PropertyRef(
        "controller_is_controller",
        description=(
            "Whether the platform that Cartography authenticates as controls "
            "the account and can use platform controls on it."
        ),
    )
    controller_requirement_collection: PropertyRef = PropertyRef(
        "controller_requirement_collection",
        description=(
            "Who collects onboarding requirements: `application` or `stripe`. "
            "Stripe returns it only to the controlling platform."
        ),
    )
    controller_fees_payer: PropertyRef = PropertyRef(
        "controller_fees_payer",
        description=(
            "Who pays Stripe fees: `account`, `application`, "
            "`application_custom`, or `application_express`."
        ),
    )
    controller_losses_payments: PropertyRef = PropertyRef(
        "controller_losses_payments",
        description="Who is liable for negative balances: `application` or `stripe`.",
    )
    controller_stripe_dashboard_type: PropertyRef = PropertyRef(
        "controller_stripe_dashboard_type",
        description=(
            "Stripe Dashboard that the account's own users can sign in to: "
            "`full`, `express`, or `none`."
        ),
    )
    charges_enabled: PropertyRef = PropertyRef(
        "charges_enabled",
        description="Whether the connected account can process charges.",
    )
    payouts_enabled: PropertyRef = PropertyRef(
        "payouts_enabled",
        description="Whether Stripe can pay out funds from the connected account.",
    )
    details_submitted: PropertyRef = PropertyRef(
        "details_submitted",
        description="Whether the connected account submitted its onboarding details.",
    )
    disabled_reason: PropertyRef = PropertyRef(
        "disabled_reason",
        description=(
            "Reason that Stripe disabled charges or payouts on the connected "
            "account. Empty when the account isn't disabled."
        ),
    )
    active_capabilities: PropertyRef = PropertyRef(
        "active_capabilities",
        description="Capabilities in the `active` state, such as `transfers`.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Unix timestamp, in seconds, when the account was connected.",
    )


@dataclass(frozen=True)
class StripeConnectedAccountToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
# (:StripeAccount)-[:RESOURCE]->(:StripeConnectedAccount)
class StripeConnectedAccountToAccountRel(CartographyRelSchema):
    """The Connect platform account has the connected account."""

    target_node_label: str = "StripeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("STRIPE_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: StripeConnectedAccountToAccountRelProperties = (
        StripeConnectedAccountToAccountRelProperties()
    )


@dataclass(frozen=True)
class StripeConnectedAccountSchema(CartographyNodeSchema):
    """
    A Stripe account connected to the platform through Stripe Connect.

    Cartography reads connected accounts from `GET /v1/accounts` only when you
    pass `--stripe-sync-connected-accounts`. It stores no email, legal-entity,
    representative, bank account, or terms-of-service acceptance data.
    """

    label: str = "StripeConnectedAccount"
    properties: StripeConnectedAccountNodeProperties = (
        StripeConnectedAccountNodeProperties()
    )
    sub_resource_relationship: StripeConnectedAccountToAccountRel = (
        StripeConnectedAccountToAccountRel()
    )
