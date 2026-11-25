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
class BasetenChainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Baseten Chain ID.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Chain name.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the Chain was created.",
    )
    deployments_count: PropertyRef = PropertyRef(
        "deployments_count",
        description="Number of deployments of the Chain.",
    )
    team_name: PropertyRef = PropertyRef(
        "team_name",
        description="Name of the team that owns the Chain.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenChainToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenChain)
class BasetenChainToOrganizationRel(CartographyRelSchema):
    """The organization contains the Chain."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenChainToOrganizationRelProperties = (
        BasetenChainToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenChainToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenTeam)-[:RESOURCE]->(:BasetenChain)
class BasetenChainToTeamRel(CartographyRelSchema):
    """The team owns the Chain."""

    target_node_label: str = "BasetenTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenChainToTeamRelProperties = BasetenChainToTeamRelProperties()


@dataclass(frozen=True)
class BasetenChainSchema(CartographyNodeSchema):
    """
    A Baseten Chain, a multi-step inference workflow made of Chainlets.

    Baseten reports the owning team by name, so Cartography links the Chain to the
    `BasetenTeam` with that name in the same organization.
    """

    label: str = "BasetenChain"
    properties: BasetenChainNodeProperties = BasetenChainNodeProperties()
    sub_resource_relationship: BasetenChainToOrganizationRel = (
        BasetenChainToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [BasetenChainToTeamRel()],
    )
