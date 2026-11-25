from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class StripeAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stripe account ID, for example `acct_1Nv0FGQ9RKHgCVdK`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description=(
            "Customer-facing business name. Falls back to the Dashboard display "
            "name, then to the account ID, when the account doesn't set one."
        ),
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Name that the Stripe Dashboard shows for the account.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description=(
            "Email address associated with the account. Stripe doesn't use it "
            "for authentication."
        ),
    )
    url: PropertyRef = PropertyRef(
        "url",
        description="Business website from the account's business profile.",
    )
    mcc: PropertyRef = PropertyRef(
        "mcc",
        description="Merchant category code of the business.",
    )
    country: PropertyRef = PropertyRef(
        "country",
        description="Two-letter country code of the account.",
    )
    default_currency: PropertyRef = PropertyRef(
        "default_currency",
        description="Three-letter ISO code of the account's default currency.",
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
            "`account` when the account controls itself, or `application` when "
            "a Connect platform controls it."
        ),
    )
    charges_enabled: PropertyRef = PropertyRef(
        "charges_enabled",
        description="Whether the account can process charges.",
    )
    payouts_enabled: PropertyRef = PropertyRef(
        "payouts_enabled",
        description="Whether Stripe can pay out funds from the account.",
    )
    details_submitted: PropertyRef = PropertyRef(
        "details_submitted",
        description="Whether the account submitted its onboarding details.",
    )
    disabled_reason: PropertyRef = PropertyRef(
        "disabled_reason",
        description=(
            "Reason that Stripe disabled charges or payouts on the account, from "
            "`requirements.disabled_reason`. Empty when the account isn't disabled."
        ),
    )
    active_capabilities: PropertyRef = PropertyRef(
        "active_capabilities",
        description="Capabilities in the `active` state, such as `card_payments`.",
    )
    decline_on_avs_failure: PropertyRef = PropertyRef(
        "decline_on_avs_failure",
        description=(
            "Whether Stripe declines card charges that fail the address (AVS) "
            "check, from `settings.card_payments.decline_on`."
        ),
    )
    decline_on_cvc_failure: PropertyRef = PropertyRef(
        "decline_on_cvc_failure",
        description=(
            "Whether Stripe declines card charges that fail the CVC check, from "
            "`settings.card_payments.decline_on`."
        ),
    )
    timezone: PropertyRef = PropertyRef(
        "timezone",
        description="IANA time zone that the Stripe Dashboard uses for the account.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Unix timestamp, in seconds, when the account was created.",
    )


@dataclass(frozen=True)
class StripeAccountSchema(CartographyNodeSchema):
    """
    The Stripe account that owns the API key Cartography authenticates with.

    Cartography reads it from `GET /v1/account`. It stores no legal-entity,
    representative, bank account, or terms-of-service acceptance data.
    """

    label: str = "StripeAccount"
    properties: StripeAccountNodeProperties = StripeAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
