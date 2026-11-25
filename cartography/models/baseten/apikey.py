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
class BasetenApiKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "prefix",
        description=(
            "API key prefix. Baseten identifies keys by prefix, for example when "
            "revoking one."
        ),
    )
    prefix: PropertyRef = PropertyRef(
        "prefix",
        extra_index=True,
        description="API key prefix. The plaintext key is never returned or stored.",
    )
    name: PropertyRef = PropertyRef("name", description="API key name, if set.")
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Key type: `PERSONAL`, `WORKSPACE_MANAGE_ALL`, `WORKSPACE_INVOKE`, "
            "`WORKSPACE_EXPORT_METRICS`, `WORKSPACE_MANAGE_API_KEYS`, or `GRID`."
        ),
    )
    team_name: PropertyRef = PropertyRef(
        "team_name",
        description="Name of the team that a team API key belongs to.",
    )
    model_ids: PropertyRef = PropertyRef(
        "model_ids",
        description=(
            "IDs of the models that a `WORKSPACE_INVOKE` or "
            "`WORKSPACE_EXPORT_METRICS` key is scoped to. Null when the key covers "
            "every model in its team."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the key was created.",
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description="ISO 8601 expiry timestamp. Null if the key never expires.",
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description=(
            "ISO 8601 timestamp of the key's last recorded use. Baseten may delay "
            "updates."
        ),
    )
    owner_user_id: PropertyRef = PropertyRef(
        "owner_user_id",
        description="ID of the user who owns a personal API key.",
    )
    owner_email: PropertyRef = PropertyRef(
        "owner_email",
        extra_index=True,
        description="Email address of the user who owns a personal API key.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenApiKey)
class BasetenApiKeyToOrganizationRel(CartographyRelSchema):
    """The organization contains the API key."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenApiKeyToOrganizationRelProperties = (
        BasetenApiKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenApiKeyToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenTeam)-[:RESOURCE]->(:BasetenApiKey)
class BasetenApiKeyToTeamRel(CartographyRelSchema):
    """The team owns the team API key."""

    target_node_label: str = "BasetenTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenApiKeyToTeamRelProperties = BasetenApiKeyToTeamRelProperties()


@dataclass(frozen=True)
class BasetenApiKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenApiKey)-[:OWNED_BY]->(:BasetenUser)
class BasetenApiKeyToUserRel(CartographyRelSchema):
    """A personal API key is owned by a user and carries that user's permissions."""

    target_node_label: str = "BasetenUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: BasetenApiKeyToUserRelProperties = BasetenApiKeyToUserRelProperties()


@dataclass(frozen=True)
class BasetenApiKeyToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenApiKey)-[:SCOPED_TO]->(:BasetenModel)
class BasetenApiKeyToModelRel(CartographyRelSchema):
    """A model-scoped team API key can invoke the model or export its metrics."""

    target_node_label: str = "BasetenModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("model_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCOPED_TO"
    properties: BasetenApiKeyToModelRelProperties = BasetenApiKeyToModelRelProperties()


@dataclass(frozen=True)
class BasetenApiKeySchema(CartographyNodeSchema):
    """
    A Baseten API key.

    Cartography ingests key metadata from `GET /v1/api_keys`; Baseten never returns
    plaintext keys. Which keys the endpoint returns depends on the configured key: an
    organization Admin's personal key or an API key management key returns every
    team key and every member's personal key, a Team Admin sees their teams' keys,
    and other users see only their own keys and the team keys they created.
    """

    label: str = "BasetenApiKey"
    properties: BasetenApiKeyNodeProperties = BasetenApiKeyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    sub_resource_relationship: BasetenApiKeyToOrganizationRel = (
        BasetenApiKeyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            BasetenApiKeyToTeamRel(),
            BasetenApiKeyToUserRel(),
            BasetenApiKeyToModelRel(),
        ],
    )
