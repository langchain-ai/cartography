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
class FireworksDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Resource name of the deployment, such as "
            "`accounts/my-account/deployments/my-deployment`."
        ),
    )
    deployment_id: PropertyRef = PropertyRef(
        "deployment_id",
        description="Deployment ID within the account.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable deployment name.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Deployment description.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Deployment state, such as `READY`, `CREATING`, or `FAILED`.",
    )
    base_model: PropertyRef = PropertyRef(
        "base_model",
        extra_index=True,
        description=(
            "Resource name of the served model, such as "
            "`accounts/fireworks/models/llama-v3p1-8b-instruct`."
        ),
    )
    accelerator_type: PropertyRef = PropertyRef(
        "accelerator_type",
        description="GPU type, such as `NVIDIA_H100_80GB`.",
    )
    accelerator_count: PropertyRef = PropertyRef(
        "accelerator_count",
        description="Number of accelerators per replica.",
    )
    precision: PropertyRef = PropertyRef(
        "precision",
        description="Serving precision, such as `FP8`.",
    )
    min_replica_count: PropertyRef = PropertyRef(
        "min_replica_count",
        description="Minimum number of replicas.",
    )
    max_replica_count: PropertyRef = PropertyRef(
        "max_replica_count",
        description="Maximum number of replicas.",
    )
    replica_count: PropertyRef = PropertyRef(
        "replica_count",
        description="Current number of replicas.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="Region where the deployment currently runs.",
    )
    direct_route_type: PropertyRef = PropertyRef(
        "direct_route_type",
        description=(
            "Direct route that bypasses the Fireworks AI API gateway: `INTERNET`, "
            "`GCP_PRIVATE_SERVICE_CONNECT`, or `AWS_PRIVATELINK`. Null when direct "
            "routing is off."
        ),
    )
    direct_route_handle: PropertyRef = PropertyRef(
        "direct_route_handle",
        description="Handle for calling the direct route, such as a hostname or service attachment.",
    )
    enable_addons: PropertyRef = PropertyRef(
        "enable_addons",
        description="Whether the deployment can serve LoRA addons.",
    )
    preemptible: PropertyRef = PropertyRef(
        "preemptible",
        description="Whether the deployment runs on preemptible capacity.",
    )
    deployment_shape: PropertyRef = PropertyRef(
        "deployment_shape",
        description="Resource name of the deployment shape version in use.",
    )
    cluster: PropertyRef = PropertyRef(
        "cluster",
        description="Resource name of the bring-your-own-cluster (BYOC) cluster that runs the deployment.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="RFC 3339 timestamp when the deployment was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="RFC 3339 timestamp when the deployment was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksDeploymentToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksDeployment)
class FireworksDeploymentToAccountRel(CartographyRelSchema):
    """The account contains the deployment."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksDeploymentToAccountRelProperties = (
        FireworksDeploymentToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksDeploymentToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksDeployment)-[:SERVES]->(:FireworksModel)
class FireworksDeploymentToModelRel(CartographyRelSchema):
    """The deployment serves a model that the account owns.

    Deployments of public catalog models keep the model only in `base_model`.
    """

    target_node_label: str = "FireworksModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("base_model")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SERVES"
    properties: FireworksDeploymentToModelRelProperties = (
        FireworksDeploymentToModelRelProperties()
    )


@dataclass(frozen=True)
class FireworksDeploymentSchema(CartographyNodeSchema):
    """A dedicated, on-demand Fireworks AI deployment that serves a model on reserved GPUs.

    Deleted deployments aren't ingested. The deployment's direct-route API keys are
    credentials and are never ingested.
    """

    label: str = "FireworksDeployment"
    properties: FireworksDeploymentNodeProperties = FireworksDeploymentNodeProperties()
    sub_resource_relationship: FireworksDeploymentToAccountRel = (
        FireworksDeploymentToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [FireworksDeploymentToModelRel()],
    )
