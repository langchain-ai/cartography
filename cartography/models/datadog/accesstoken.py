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
class DatadogAccessTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Datadog access token ID.")
    name: PropertyRef = PropertyRef("name", description="Access token name.")
    token_type: PropertyRef = PropertyRef(
        "token_type",
        description=(
            "`personal` for a personal access token (PAT) or `service` for a "
            "service access token (SAT)."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time that the token was created.",
    )
    modified_at: PropertyRef = PropertyRef(
        "modified_at",
        description="Time that the token was last modified.",
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description="Time that the token expires. `null` means that it doesn't expire.",
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description="Time that the token was last used, if Datadog reports it.",
    )
    scopes: PropertyRef = PropertyRef(
        "scopes",
        description="Sorted list of authorization scopes granted to the token.",
    )
    leaked: PropertyRef = PropertyRef(
        "leaked",
        description=(
            "Whether Datadog detected the token in a leak. `null` when the "
            "response didn't include leak information."
        ),
    )
    owner_id: PropertyRef = PropertyRef(
        "owner_id",
        description="ID of the user or service account that owns the token.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatadogAccessTokenToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogOrganization)-[:RESOURCE]->(:DatadogAccessToken)
class DatadogAccessTokenToOrganizationRel(CartographyRelSchema):
    """The organization contains the access token."""

    target_node_label: str = "DatadogOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatadogAccessTokenToOrganizationRelProperties = (
        DatadogAccessTokenToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class DatadogAccessTokenToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogAccessToken)-[:OWNED_BY]->(:DatadogUser)
class DatadogAccessTokenToUserRel(CartographyRelSchema):
    """The personal access token is owned by the user."""

    target_node_label: str = "DatadogUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: DatadogAccessTokenToUserRelProperties = (
        DatadogAccessTokenToUserRelProperties()
    )


@dataclass(frozen=True)
class DatadogAccessTokenToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatadogAccessToken)-[:OWNED_BY]->(:DatadogServiceAccount)
class DatadogAccessTokenToServiceAccountRel(CartographyRelSchema):
    """The service access token is owned by the service account."""

    target_node_label: str = "DatadogServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: DatadogAccessTokenToServiceAccountRelProperties = (
        DatadogAccessTokenToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class DatadogAccessTokenSchema(CartographyNodeSchema):
    """Metadata of a Datadog access token, read from `GET /api/v2/personal_access_tokens`.

    The listing returns personal access tokens (PATs), owned by users, and
    service access tokens (SATs), owned by service accounts. Tokens
    authenticate without an API key. Cartography syncs tokens only when it can
    also list every application key, which proves the `org_app_keys_read`
    permission, and it doesn't store the token's public portion or secret.
    """

    label: str = "DatadogAccessToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: DatadogAccessTokenNodeProperties = DatadogAccessTokenNodeProperties()
    sub_resource_relationship: DatadogAccessTokenToOrganizationRel = (
        DatadogAccessTokenToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatadogAccessTokenToUserRel(), DatadogAccessTokenToServiceAccountRel()],
    )
