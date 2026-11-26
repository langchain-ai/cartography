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
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class DatadogServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Datadog user ID of the service account.",
    )
    name: PropertyRef = PropertyRef("name", description="Service account name.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Notification email address of the service account.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Account status: `Active` or `Disabled`.",
    )
    disabled: PropertyRef = PropertyRef(
        "disabled",
        description=(
            "Whether the service account is disabled and its credentials "
            "stop working."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time that the service account was created.",
    )
    modified_at: PropertyRef = PropertyRef(
        "modified_at",
        description="Time that the service account was last modified.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatadogServiceAccountToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogOrganization)-[:RESOURCE]->(:DatadogServiceAccount)
class DatadogServiceAccountToOrganizationRel(CartographyRelSchema):
    """The organization contains the service account."""

    target_node_label: str = "DatadogOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatadogServiceAccountToOrganizationRelProperties = (
        DatadogServiceAccountToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class DatadogServiceAccountToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogServiceAccount)-[:HAS_ROLE]->(:DatadogRole)
class DatadogServiceAccountToRoleRel(CartographyRelSchema):
    """The service account holds the role."""

    target_node_label: str = "DatadogRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: DatadogServiceAccountToRoleRelProperties = (
        DatadogServiceAccountToRoleRelProperties()
    )


@dataclass(frozen=True)
class DatadogServiceAccountSchema(CartographyNodeSchema):
    """A Datadog service account, read from `GET /api/v2/users`.

    Datadog lists service accounts with users and marks them with
    `service_account: true`. Service accounts can't sign in. Cartography keeps
    identity and lifecycle metadata and role memberships; it doesn't collect
    the service account's keys or tokens.
    """

    label: str = "DatadogServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    properties: DatadogServiceAccountNodeProperties = (
        DatadogServiceAccountNodeProperties()
    )
    sub_resource_relationship: DatadogServiceAccountToOrganizationRel = (
        DatadogServiceAccountToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatadogServiceAccountToRoleRel()],
    )
