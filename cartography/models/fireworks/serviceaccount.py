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
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class FireworksServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Resource name of the service account, such as "
            "`accounts/my-account/users/ci-bot`."
        ),
    )
    user_id: PropertyRef = PropertyRef(
        "user_id",
        description="Service account ID within the account.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable service account name.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description=(
            "Service account email address, such as "
            "`ci-bot@my-account.sa.fireworks.ai`. Audit logs use this address."
        ),
    )
    role: PropertyRef = PropertyRef(
        "role",
        description=(
            "Account role: `admin`, `user`, `contributor`, `inference-user`, or `custom`. "
            "Service accounts default to `inference-user`."
        ),
    )
    permission_preset: PropertyRef = PropertyRef(
        "permission_preset",
        description="Permission preset that governs the service account when `role` is `custom`.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Service account state, such as `READY`.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="RFC 3339 timestamp when the service account was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="RFC 3339 timestamp when the service account was last updated.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="ID of the Fireworks AI account that the service account belongs to.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksServiceAccountToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksServiceAccount)
class FireworksServiceAccountToAccountRel(CartographyRelSchema):
    """The account contains the service account."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksServiceAccountToAccountRelProperties = (
        FireworksServiceAccountToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksServiceAccountSchema(CartographyNodeSchema):
    """A Fireworks AI service account, a non-human user that can only authenticate with API keys."""

    label: str = "FireworksServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    properties: FireworksServiceAccountNodeProperties = (
        FireworksServiceAccountNodeProperties()
    )
    sub_resource_relationship: FireworksServiceAccountToAccountRel = (
        FireworksServiceAccountToAccountRel()
    )
