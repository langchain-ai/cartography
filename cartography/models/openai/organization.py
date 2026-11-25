from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class OpenAIOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="OpenAI organization ID.")
    data_retention: PropertyRef = PropertyRef(
        "data_retention",
        description=(
            "Organization data retention control: `zero_data_retention`, "
            "`modified_abuse_monitoring`, `enhanced_zero_data_retention`, or "
            "`enhanced_modified_abuse_monitoring`. Null when the Admin API key "
            "cannot read it."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIOrganizationSchema(CartographyNodeSchema):
    """An OpenAI organization containing users, projects, and admin API keys."""

    label: str = "OpenAIOrganization"
    properties: OpenAIOrganizationNodeProperties = OpenAIOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
