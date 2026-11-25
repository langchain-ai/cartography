from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class AnthropicOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic organization ID.")
    api_zero_data_retention_enabled: PropertyRef = PropertyRef(
        "api_zero_data_retention_enabled",
        description=(
            "Whether zero data retention is in place for the Claude API at the "
            "organization level. Set only when Cartography has a Compliance "
            "Access Key; null when the setting isn't reported."
        ),
    )
    claude_code_zero_data_retention_enabled: PropertyRef = PropertyRef(
        "claude_code_zero_data_retention_enabled",
        description=(
            "Whether zero data retention is in place for Claude Code in a Claude "
            "Enterprise organization. Set only when Cartography has a Compliance "
            "Access Key; null when the setting isn't reported."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicOrganizationSchema(CartographyNodeSchema):
    """An Anthropic organization containing users, workspaces, and API keys."""

    label: str = "AnthropicOrganization"
    properties: AnthropicOrganizationNodeProperties = (
        AnthropicOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
