from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import THIRD_PARTY_APP


@dataclass(frozen=True)
class StripeAppInstallNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="App install ID, for example `appinst_61VGZmT4pXc8Rk2w41LUZiLcTVChK7Ab`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    app_id: PropertyRef = PropertyRef(
        "app_id",
        extra_index=True,
        description=(
            "ID of the installed Stripe App. Stripe's install object doesn't "
            "include the app's name."
        ),
    )
    channel: PropertyRef = PropertyRef(
        "channel",
        description=(
            "Distribution channel: `public`, `private_live`, `private_test`, "
            "`testing`, or `review`."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status",
        description=(
            "Install status, such as `installed`, `installing`, or "
            "`uninstall_failed`."
        ),
    )
    approval_required: PropertyRef = PropertyRef(
        "approval_required",
        description=(
            "Whether the app's latest version requests permissions, endpoints, "
            "or content security policy entries that the account hasn't approved."
        ),
    )
    permissions_granted: PropertyRef = PropertyRef(
        "permissions_granted",
        description="Permissions that the account granted, such as `customer_read`.",
    )
    permissions_pending: PropertyRef = PropertyRef(
        "permissions_pending",
        description="Permissions that the app requests but the account hasn't granted.",
    )
    endpoints_granted: PropertyRef = PropertyRef(
        "endpoints_granted",
        description="Endpoint URLs that the account authorized the app to use.",
    )
    endpoints_pending: PropertyRef = PropertyRef(
        "endpoints_pending",
        description="Endpoint URLs that the app requests but the account hasn't authorized.",
    )
    connect_src_granted: PropertyRef = PropertyRef(
        "connect_src_granted",
        description=(
            "URLs that the app's UI can make network requests to, from the "
            "granted content security policy."
        ),
    )
    image_src_granted: PropertyRef = PropertyRef(
        "image_src_granted",
        description=(
            "URLs that the app's UI can load images from, from the granted "
            "content security policy."
        ),
    )
    created_by: PropertyRef = PropertyRef(
        "created_by",
        description="ID of the embedding platform that created the install, if any.",
    )
    livemode: PropertyRef = PropertyRef(
        "livemode",
        description="Whether the install exists in live mode.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Unix timestamp, in seconds, when the app was installed.",
    )


@dataclass(frozen=True)
class StripeAppInstallToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
# (:StripeAccount)-[:RESOURCE]->(:StripeAppInstall)
class StripeAppInstallToAccountRel(CartographyRelSchema):
    """The Stripe account has the app installed."""

    target_node_label: str = "StripeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("STRIPE_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: StripeAppInstallToAccountRelProperties = (
        StripeAppInstallToAccountRelProperties()
    )


@dataclass(frozen=True)
class StripeAppInstallSchema(CartographyNodeSchema):
    """
    A Stripe App installed on the account, with the permissions, endpoints, and
    content security policy entries that the account granted it, from
    `GET /v1/apps/installs`.

    Cartography drops the install's OAuth authorization code.
    """

    label: str = "StripeAppInstall"
    properties: StripeAppInstallNodeProperties = StripeAppInstallNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([THIRD_PARTY_APP])
    sub_resource_relationship: StripeAppInstallToAccountRel = (
        StripeAppInstallToAccountRel()
    )
