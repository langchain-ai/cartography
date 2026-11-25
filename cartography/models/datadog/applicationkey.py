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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class DatadogApplicationKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Datadog application key ID.")
    name: PropertyRef = PropertyRef("name", description="Application key name.")
    last4: PropertyRef = PropertyRef(
        "last4",
        description="Last four characters of the key. Cartography never reads the key.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time that the key was created.",
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description="Time that the key was last used, if Datadog reports it.",
    )
    scopes: PropertyRef = PropertyRef(
        "scopes",
        description=(
            "Sorted list of authorization scopes. `null` means that the key is "
            "unscoped and has every permission of its owner."
        ),
    )
    is_scoped: PropertyRef = PropertyRef(
        "is_scoped",
        description="Whether the key is limited to authorization scopes.",
    )
    leaked: PropertyRef = PropertyRef(
        "leaked",
        description=(
            "Whether Datadog detected the key in a leak. `null` when the "
            "response didn't include leak information."
        ),
    )
    owner_id: PropertyRef = PropertyRef(
        "owner_id",
        description="ID of the user or service account that owns the key.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatadogApplicationKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogOrganization)-[:RESOURCE]->(:DatadogApplicationKey)
class DatadogApplicationKeyToOrganizationRel(CartographyRelSchema):
    """The organization contains the application key."""

    target_node_label: str = "DatadogOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatadogApplicationKeyToOrganizationRelProperties = (
        DatadogApplicationKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class DatadogApplicationKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogApplicationKey)-[:OWNED_BY]->(:DatadogUser)
class DatadogApplicationKeyToUserRel(CartographyRelSchema):
    """The application key is owned by the user."""

    target_node_label: str = "DatadogUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: DatadogApplicationKeyToUserRelProperties = (
        DatadogApplicationKeyToUserRelProperties()
    )


@dataclass(frozen=True)
class DatadogApplicationKeyToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogApplicationKey)-[:OWNED_BY]->(:DatadogServiceAccount)
class DatadogApplicationKeyToServiceAccountRel(CartographyRelSchema):
    """The application key is owned by the service account."""

    target_node_label: str = "DatadogServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: DatadogApplicationKeyToServiceAccountRelProperties = (
        DatadogApplicationKeyToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class DatadogApplicationKeySchema(CartographyNodeSchema):
    """Metadata of a Datadog application key, read from `GET /api/v2/application_keys`.

    An application key acts with the permissions of its owner, limited to its
    scopes if it has any. The organization-wide listing includes keys owned by
    service accounts. The list endpoint doesn't return key values, and
    Cartography never calls the single-key endpoints that can.
    """

    label: str = "DatadogApplicationKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: DatadogApplicationKeyNodeProperties = (
        DatadogApplicationKeyNodeProperties()
    )
    sub_resource_relationship: DatadogApplicationKeyToOrganizationRel = (
        DatadogApplicationKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatadogApplicationKeyToUserRel(),
            DatadogApplicationKeyToServiceAccountRel(),
        ],
    )
