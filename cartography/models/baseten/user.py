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
class BasetenUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("user_id", description="Baseten user ID.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address of the user.",
    )
    name: PropertyRef = PropertyRef("name", description="Display name of the user.")
    workspace_name: PropertyRef = PropertyRef(
        "workspace_name",
        description="Name of the user's workspace.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenUser)
class BasetenUserToOrganizationRel(CartographyRelSchema):
    """The organization contains the user."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenUserToOrganizationRelProperties = (
        BasetenUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenUserSchema(CartographyNodeSchema):
    """
    A member of a Baseten organization.

    Cartography ingests joined members from `GET /v1/users`. Baseten excludes invited
    users, pending join requests, and service accounts from that list. The
    `UserAccount` label links the user to other identities with the same email.
    """

    label: str = "BasetenUser"
    properties: BasetenUserNodeProperties = BasetenUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: BasetenUserToOrganizationRel = (
        BasetenUserToOrganizationRel()
    )
