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
from cartography.models.ontology.labels import AI_MODEL


@dataclass(frozen=True)
class BasetenModelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Baseten model ID.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Model name, unique in its team.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the model was created.",
    )
    deployments_count: PropertyRef = PropertyRef(
        "deployments_count",
        description="Number of deployments of the model.",
    )
    production_deployment_id: PropertyRef = PropertyRef(
        "production_deployment_id",
        description="ID of the model's production deployment, if any.",
    )
    development_deployment_id: PropertyRef = PropertyRef(
        "development_deployment_id",
        description="ID of the model's development deployment, if any.",
    )
    instance_type_name: PropertyRef = PropertyRef(
        "instance_type_name",
        description="Instance type of the model's production deployment.",
    )
    team_name: PropertyRef = PropertyRef(
        "team_name",
        description="Name of the team that owns the model.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenModelToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenModel)
class BasetenModelToOrganizationRel(CartographyRelSchema):
    """The organization contains the model."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenModelToOrganizationRelProperties = (
        BasetenModelToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenModelToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenTeam)-[:RESOURCE]->(:BasetenModel)
class BasetenModelToTeamRel(CartographyRelSchema):
    """The team owns the model."""

    target_node_label: str = "BasetenTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenModelToTeamRelProperties = BasetenModelToTeamRelProperties()


@dataclass(frozen=True)
class BasetenModelSchema(CartographyNodeSchema):
    """
    A model deployed on Baseten Dedicated Inference.

    A model groups the deployments of one inference service and belongs to a team.
    Baseten reports the owning team by name, so Cartography links the model to the
    `BasetenTeam` with that name in the same organization.
    """

    label: str = "BasetenModel"
    properties: BasetenModelNodeProperties = BasetenModelNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AI_MODEL])
    sub_resource_relationship: BasetenModelToOrganizationRel = (
        BasetenModelToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [BasetenModelToTeamRel()],
    )
