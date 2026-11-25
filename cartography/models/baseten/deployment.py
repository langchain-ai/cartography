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
class BasetenDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Baseten deployment ID.")
    name: PropertyRef = PropertyRef("name", description="Deployment name.")
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the deployment was created.",
    )
    model_id: PropertyRef = PropertyRef(
        "model_id",
        extra_index=True,
        description="ID of the model that the deployment belongs to.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Deployment status, such as `ACTIVE`, `SCALED_TO_ZERO`, or `INACTIVE`.",
    )
    is_production: PropertyRef = PropertyRef(
        "is_production",
        description="Whether the deployment is the model's production deployment.",
    )
    is_development: PropertyRef = PropertyRef(
        "is_development",
        description="Whether the deployment is the model's development deployment.",
    )
    environment: PropertyRef = PropertyRef(
        "environment",
        description="Name of the environment the deployment serves, if any.",
    )
    instance_type_name: PropertyRef = PropertyRef(
        "instance_type_name",
        description="Instance type the deployment runs on.",
    )
    active_replica_count: PropertyRef = PropertyRef(
        "active_replica_count",
        description="Number of active replicas.",
    )
    min_replica: PropertyRef = PropertyRef(
        "min_replica",
        description="Minimum number of replicas from the autoscaling settings.",
    )
    max_replica: PropertyRef = PropertyRef(
        "max_replica",
        description="Maximum number of replicas from the autoscaling settings.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="Slug of the region selected for the deployment, if any.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenDeploymentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenDeployment)
class BasetenDeploymentToOrganizationRel(CartographyRelSchema):
    """The organization contains the deployment."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenDeploymentToOrganizationRelProperties = (
        BasetenDeploymentToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenDeploymentToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenModel)-[:HAS_DEPLOYMENT]->(:BasetenDeployment)
class BasetenDeploymentToModelRel(CartographyRelSchema):
    """The model has the deployment."""

    target_node_label: str = "BasetenModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("model_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEPLOYMENT"
    properties: BasetenDeploymentToModelRelProperties = (
        BasetenDeploymentToModelRelProperties()
    )


@dataclass(frozen=True)
class BasetenDeploymentSchema(CartographyNodeSchema):
    """
    A deployment of a Baseten model: one version of the model's code, weights, and
    configuration running on an instance type.
    """

    label: str = "BasetenDeployment"
    properties: BasetenDeploymentNodeProperties = BasetenDeploymentNodeProperties()
    sub_resource_relationship: BasetenDeploymentToOrganizationRel = (
        BasetenDeploymentToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [BasetenDeploymentToModelRel()],
    )
