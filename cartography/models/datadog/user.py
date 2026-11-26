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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class DatadogUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Datadog user ID.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address of the user, which links the account to a `User`.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Account status: `Active`, `Pending`, or `Disabled`.",
    )
    disabled: PropertyRef = PropertyRef(
        "disabled",
        description="Whether the user is disabled and can't sign in.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time that the user was created.",
    )
    modified_at: PropertyRef = PropertyRef(
        "modified_at",
        description="Time that the user was last modified.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatadogUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogOrganization)-[:RESOURCE]->(:DatadogUser)
class DatadogUserToOrganizationRel(CartographyRelSchema):
    """The organization contains the user."""

    target_node_label: str = "DatadogOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatadogUserToOrganizationRelProperties = (
        DatadogUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class DatadogUserToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogUser)-[:HAS_ROLE]->(:DatadogRole)
class DatadogUserToRoleRel(CartographyRelSchema):
    """The user holds the role."""

    target_node_label: str = "DatadogRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: DatadogUserToRoleRelProperties = DatadogUserToRoleRelProperties()


@dataclass(frozen=True)
class DatadogUserSchema(CartographyNodeSchema):
    """A person's account in a Datadog organization, read from `GET /api/v2/users`.

    Cartography includes pending and disabled users so that stale access stays
    visible. It keeps only account identity and lifecycle fields; it doesn't
    collect profile or sign-in details such as the person's name, title, icon,
    MFA state, or last sign-in. Entries that Datadog marks as service accounts
    load as `DatadogServiceAccount` instead. The `UserAccount` label links the
    user to the canonical `User` node by email address.
    """

    label: str = "DatadogUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: DatadogUserNodeProperties = DatadogUserNodeProperties()
    sub_resource_relationship: DatadogUserToOrganizationRel = (
        DatadogUserToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatadogUserToRoleRel()],
    )
