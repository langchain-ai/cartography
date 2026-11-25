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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class BasetenTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Baseten team ID.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Team name, unique in the organization.",
    )
    default: PropertyRef = PropertyRef(
        "default",
        description="Whether this is the organization's default team.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the team was created.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenTeamToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenTeam)
class BasetenTeamToOrganizationRel(CartographyRelSchema):
    """The organization contains the team."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenTeamToOrganizationRelProperties = (
        BasetenTeamToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenTeamSchema(CartographyNodeSchema):
    """
    A team in a Baseten organization.

    Teams isolate models, Chains, secrets, team API keys, and restricted environments.
    Every organization has a default team; organizations on the Enterprise plan can
    create more. Cartography ingests the teams that the API key can access.
    """

    label: str = "BasetenTeam"
    properties: BasetenTeamNodeProperties = BasetenTeamNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: BasetenTeamToOrganizationRel = (
        BasetenTeamToOrganizationRel()
    )
