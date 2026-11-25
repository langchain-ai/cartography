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
from cartography.models.ontology.labels import AI_MODEL


@dataclass(frozen=True)
class FireworksModelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Resource name of the model, such as `accounts/my-account/models/my-model`.",
    )
    model_id: PropertyRef = PropertyRef(
        "model_id",
        description="Model ID within the account.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable model name.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Model description.",
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description="Model kind, such as `HF_BASE_MODEL`, `HF_PEFT_ADDON`, or `CUSTOM_MODEL`.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Model state: `UPLOADING` or `READY`.",
    )
    public: PropertyRef = PropertyRef(
        "public",
        description="Whether any Fireworks AI account can read the model.",
    )
    base_model: PropertyRef = PropertyRef(
        "base_model",
        description="Resource name of the base model that a LoRA or other addon model extends.",
    )
    imported_from: PropertyRef = PropertyRef(
        "imported_from",
        description="Resource name of the model this one was imported from.",
    )
    fine_tuning_job: PropertyRef = PropertyRef(
        "fine_tuning_job",
        description="Resource name of the fine-tuning job that created the model.",
    )
    hugging_face_url: PropertyRef = PropertyRef(
        "hugging_face_url",
        description="URL of the model on Hugging Face.",
    )
    github_url: PropertyRef = PropertyRef(
        "github_url",
        description="URL of the model's GitHub repository.",
    )
    encryption_state: PropertyRef = PropertyRef(
        "encryption_state",
        description="Encryption at rest: `ENCRYPTION_STATE_PLAINTEXT` or `ENCRYPTION_STATE_CMEK`.",
    )
    cluster: PropertyRef = PropertyRef(
        "cluster",
        description="Resource name of the bring-your-own-cluster (BYOC) cluster that holds the model.",
    )
    context_length: PropertyRef = PropertyRef(
        "context_length",
        description="Maximum context length the model supports.",
    )
    supports_tools: PropertyRef = PropertyRef(
        "supports_tools",
        description="Whether the model accepts tool definitions.",
    )
    supports_image_input: PropertyRef = PropertyRef(
        "supports_image_input",
        description="Whether the model accepts image input.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="RFC 3339 timestamp when the model was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="RFC 3339 timestamp when the model was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksModelToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksModel)
class FireworksModelToAccountRel(CartographyRelSchema):
    """The account contains the model."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksModelToAccountRelProperties = (
        FireworksModelToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksModelSchema(CartographyNodeSchema):
    """A model owned by a Fireworks AI account, such as an uploaded base model or a fine-tuned LoRA.

    The public Fireworks AI catalog under `accounts/fireworks` isn't ingested.
    """

    label: str = "FireworksModel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AI_MODEL])
    properties: FireworksModelNodeProperties = FireworksModelNodeProperties()
    sub_resource_relationship: FireworksModelToAccountRel = FireworksModelToAccountRel()
