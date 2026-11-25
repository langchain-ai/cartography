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
class DatadogAPIKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Datadog API key ID.")
    name: PropertyRef = PropertyRef("name", description="API key name.")
    last4: PropertyRef = PropertyRef(
        "last4",
        description="Last four characters of the key. Cartography never reads the key.",
    )
    category: PropertyRef = PropertyRef(
        "category",
        description="API key category, for example `default`.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time that the key was created.",
    )
    modified_at: PropertyRef = PropertyRef(
        "modified_at",
        description="Time that the key was last modified.",
    )
    date_last_used: PropertyRef = PropertyRef(
        "date_last_used",
        description="Time that the key was last used, if Datadog reports it.",
    )
    remote_config_read_enabled: PropertyRef = PropertyRef(
        "remote_config_read_enabled",
        description="Whether the key can read Remote Configuration.",
    )
    leaked: PropertyRef = PropertyRef(
        "leaked",
        description=(
            "Whether Datadog detected the key in a leak. `null` when the "
            "response didn't include leak information."
        ),
    )
    created_by_id: PropertyRef = PropertyRef(
        "created_by_id",
        description="ID of the user or service account that created the key.",
    )
    modified_by_id: PropertyRef = PropertyRef(
        "modified_by_id",
        description="ID of the user or service account that last modified the key.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatadogAPIKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogOrganization)-[:RESOURCE]->(:DatadogAPIKey)
class DatadogAPIKeyToOrganizationRel(CartographyRelSchema):
    """The organization contains the API key."""

    target_node_label: str = "DatadogOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatadogAPIKeyToOrganizationRelProperties = (
        DatadogAPIKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class DatadogUserToAPIKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogUser)-[:CREATED]->(:DatadogAPIKey)
class DatadogUserToAPIKeyRel(CartographyRelSchema):
    """The user created the API key. API keys belong to the organization."""

    target_node_label: str = "DatadogUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED"
    properties: DatadogUserToAPIKeyRelProperties = DatadogUserToAPIKeyRelProperties()


@dataclass(frozen=True)
class DatadogServiceAccountToAPIKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogServiceAccount)-[:CREATED]->(:DatadogAPIKey)
class DatadogServiceAccountToAPIKeyRel(CartographyRelSchema):
    """The service account created the API key."""

    target_node_label: str = "DatadogServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED"
    properties: DatadogServiceAccountToAPIKeyRelProperties = (
        DatadogServiceAccountToAPIKeyRelProperties()
    )


@dataclass(frozen=True)
class DatadogAPIKeySchema(CartographyNodeSchema):
    """Metadata of a Datadog API key, read from `GET /api/v2/api_keys`.

    API keys submit telemetry and pair with application keys to call the API.
    They belong to the organization, not to the user who created them, so they
    keep working after that user is disabled. The list endpoint doesn't return
    key values, and Cartography never calls the single-key endpoint that does.
    """

    label: str = "DatadogAPIKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: DatadogAPIKeyNodeProperties = DatadogAPIKeyNodeProperties()
    sub_resource_relationship: DatadogAPIKeyToOrganizationRel = (
        DatadogAPIKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatadogUserToAPIKeyRel(), DatadogServiceAccountToAPIKeyRel()],
    )
