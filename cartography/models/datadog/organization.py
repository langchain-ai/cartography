from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class DatadogOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Datadog organization ID.")
    name: PropertyRef = PropertyRef("name", description="Organization name.")
    public_id: PropertyRef = PropertyRef(
        "public_id",
        extra_index=True,
        description="Public ID of the organization.",
    )
    api_base_url: PropertyRef = PropertyRef(
        "api_base_url",
        description=(
            "Datadog API base URL that the organization was read from, which "
            "identifies its site, for example `https://api.datadoghq.eu`."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatadogOrganizationSchema(CartographyNodeSchema):
    """A Datadog organization, read from `GET /api/v2/current_user`.

    The organization is the tenant for every other Datadog node. Cartography
    reads only access governance data: users, service accounts, roles, role
    memberships, and role permissions. It doesn't collect API keys,
    application keys, access tokens, or logs, and it never writes to Datadog.
    """

    label: str = "DatadogOrganization"
    properties: DatadogOrganizationNodeProperties = DatadogOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
