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
    name: PropertyRef = PropertyRef("name", description="User display name.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address of the user.",
    )
    handle: PropertyRef = PropertyRef(
        "handle",
        extra_index=True,
        description="User handle, which is usually the sign-in email address.",
    )
    title: PropertyRef = PropertyRef("title", description="Job title of the user.")
    status: PropertyRef = PropertyRef(
        "status",
        description="Account status: `Active`, `Pending`, or `Disabled`.",
    )
    disabled: PropertyRef = PropertyRef(
        "disabled",
        description="Whether the user is disabled and can't sign in.",
    )
    verified: PropertyRef = PropertyRef(
        "verified",
        description="Whether the user verified their email address.",
    )
    mfa_enabled: PropertyRef = PropertyRef(
        "mfa_enabled",
        description=(
            "Whether the user enabled Datadog multi-factor authentication. "
            "Doesn't reflect MFA enforced by a SAML identity provider."
        ),
    )
    allowed_login_methods: PropertyRef = PropertyRef(
        "allowed_login_methods",
        description=(
            "IDs of the login methods that the user may use. An empty list "
            "means that the organization default applies."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time that the user was created.",
    )
    modified_at: PropertyRef = PropertyRef(
        "modified_at",
        description="Time that the user was last modified.",
    )
    last_login_time: PropertyRef = PropertyRef(
        "last_login_time",
        description="Time of the user's most recent sign-in, if Datadog reports it.",
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
    visible. Entries that Datadog marks as service accounts load as
    `DatadogServiceAccount` instead. The `UserAccount` label links the user to
    the canonical `User` node by email address.
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
