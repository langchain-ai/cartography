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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class FireworksUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Resource name of the user, such as `accounts/my-account/users/alice`.",
    )
    user_id: PropertyRef = PropertyRef(
        "user_id",
        description="User ID within the account.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable user name.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="User email address.",
    )
    role: PropertyRef = PropertyRef(
        "role",
        description="Account role: `admin`, `user`, `contributor`, `inference-user`, or `custom`.",
    )
    permission_preset: PropertyRef = PropertyRef(
        "permission_preset",
        description="Permission preset that governs the user when `role` is `custom`.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="User state, such as `READY`.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="RFC 3339 timestamp when the user was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="RFC 3339 timestamp when the user was last updated.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="ID of the Fireworks AI account that the user belongs to.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksUserToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksUser)
class FireworksUserToAccountRel(CartographyRelSchema):
    """The account contains the user."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksUserToAccountRelProperties = (
        FireworksUserToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksUserSchema(CartographyNodeSchema):
    """A human user in a Fireworks AI account.

    Service accounts come from the same API and are ingested as
    `FireworksServiceAccount` instead.
    """

    label: str = "FireworksUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: FireworksUserNodeProperties = FireworksUserNodeProperties()
    sub_resource_relationship: FireworksUserToAccountRel = FireworksUserToAccountRel()
