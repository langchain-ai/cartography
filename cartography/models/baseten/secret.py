from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class BasetenSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Baseten secret ID. It stays the same when the secret is rotated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Secret name.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the secret was created.",
    )
    team_name: PropertyRef = PropertyRef(
        "team_name",
        description="Name of the team that owns the secret.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenSecretToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenSecret)
class BasetenSecretToOrganizationRel(CartographyRelSchema):
    """The organization contains the secret."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenSecretToOrganizationRelProperties = (
        BasetenSecretToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenSecretToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenTeam)-[:RESOURCE]->(:BasetenSecret)
class BasetenSecretToTeamRel(CartographyRelSchema):
    """The team owns the secret. Only the team's models and Chains can read it."""

    target_node_label: str = "BasetenTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenSecretToTeamRelProperties = BasetenSecretToTeamRelProperties()


@dataclass(frozen=True)
class BasetenSecretSchema(CartographyNodeSchema):
    """
    A Baseten secret that models, Chains, and training jobs read at runtime.

    Cartography ingests secret metadata only. The Management API never returns secret
    values, so none are stored in the graph.
    """

    label: str = "BasetenSecret"
    properties: BasetenSecretNodeProperties = BasetenSecretNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    sub_resource_relationship: BasetenSecretToOrganizationRel = (
        BasetenSecretToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [BasetenSecretToTeamRel()],
    )
