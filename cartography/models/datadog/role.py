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
from cartography.models.ontology.labels import PERMISSION_ROLE


@dataclass(frozen=True)
class DatadogRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Datadog role ID.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description=(
            "Role name, for example `Datadog Admin Role`. Datadog doesn't "
            "require role names to be unique."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time that the role was created.",
    )
    modified_at: PropertyRef = PropertyRef(
        "modified_at",
        description="Time that the role was last modified.",
    )
    user_count: PropertyRef = PropertyRef(
        "user_count",
        description="Number of users and service accounts that hold the role.",
    )
    permissions: PropertyRef = PropertyRef(
        "permissions",
        description=(
            "Sorted list of permission names that the role grants, for example "
            "`user_access_read`. A permission that `GET /api/v2/permissions` "
            "doesn't list keeps its ID."
        ),
    )
    receives_permissions_from: PropertyRef = PropertyRef(
        "receives_permissions_from",
        description=(
            "Managed roles from which the role automatically inherits new "
            "permissions."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatadogRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogOrganization)-[:RESOURCE]->(:DatadogRole)
class DatadogRoleToOrganizationRel(CartographyRelSchema):
    """The organization contains the role."""

    target_node_label: str = "DatadogOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatadogRoleToOrganizationRelProperties = (
        DatadogRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class DatadogRoleSchema(CartographyNodeSchema):
    """A role in a Datadog organization, read from `GET /api/v2/roles`.

    Permission names come from `GET /api/v2/permissions`. Datadog doesn't flag
    managed roles, so Cartography doesn't record whether a role is built in.
    """

    label: str = "DatadogRole"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    properties: DatadogRoleNodeProperties = DatadogRoleNodeProperties()
    sub_resource_relationship: DatadogRoleToOrganizationRel = (
        DatadogRoleToOrganizationRel()
    )
