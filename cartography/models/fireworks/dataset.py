from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class FireworksDatasetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Resource name of the dataset, such as `accounts/my-account/datasets/my-dataset`.",
    )
    dataset_id: PropertyRef = PropertyRef(
        "dataset_id",
        description="Dataset ID within the account.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable dataset name.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Dataset state: `UPLOADING` or `READY`.",
    )
    format: PropertyRef = PropertyRef(
        "format",
        description="Dataset format: `CHAT`, `COMPLETION`, or `RL`.",
    )
    example_count: PropertyRef = PropertyRef(
        "example_count",
        description="Number of examples in the dataset.",
    )
    estimated_token_count: PropertyRef = PropertyRef(
        "estimated_token_count",
        description="Estimated number of tokens in the dataset.",
    )
    external_url: PropertyRef = PropertyRef(
        "external_url",
        description="External bucket URI that holds the data, such as `gs://bucket/path.jsonl`.",
    )
    created_by: PropertyRef = PropertyRef(
        "created_by",
        description="Email address of the user who created the dataset.",
    )
    source_job_name: PropertyRef = PropertyRef(
        "source_job_name",
        description="Resource name of the job that produced the dataset, such as a batch inference job.",
    )
    encryption_state: PropertyRef = PropertyRef(
        "encryption_state",
        description="Encryption at rest: `ENCRYPTION_STATE_PLAINTEXT` or `ENCRYPTION_STATE_CMEK`.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="RFC 3339 timestamp when the dataset was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="RFC 3339 timestamp when the dataset was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksDatasetToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksDataset)
class FireworksDatasetToAccountRel(CartographyRelSchema):
    """The account contains the dataset."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksDatasetToAccountRelProperties = (
        FireworksDatasetToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksDatasetSchema(CartographyNodeSchema):
    """A dataset of training or evaluation data in a Fireworks AI account.

    Cartography records dataset metadata only, never its contents.
    """

    label: str = "FireworksDataset"
    properties: FireworksDatasetNodeProperties = FireworksDatasetNodeProperties()
    sub_resource_relationship: FireworksDatasetToAccountRel = (
        FireworksDatasetToAccountRel()
    )
