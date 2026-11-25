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
class FireworksApiKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fireworks AI API key ID.")
    name: PropertyRef = PropertyRef(
        "name",
        description="API key display name. Fireworks AI uses `default` when none is set.",
    )
    prefix: PropertyRef = PropertyRef(
        "prefix",
        description="First characters of the key, used to identify it visually.",
    )
    owner_email: PropertyRef = PropertyRef(
        "owner_email",
        extra_index=True,
        description="Email address of the user or service account that owns the key.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the key was created.",
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description="RFC 3339 timestamp when the key expires. Keys last at most one year.",
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description="RFC 3339 timestamp when the key was last used. Null if it was never used.",
    )
    secure: PropertyRef = PropertyRef(
        "secure",
        description="Whether Fireworks AI does not know the key's plaintext value.",
    )
    is_firepass: PropertyRef = PropertyRef(
        "is_firepass",
        description="Whether the key is a FirePass inference key.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksApiKeyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksApiKey)
class FireworksApiKeyToAccountRel(CartographyRelSchema):
    """The account contains the API key."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksApiKeyToAccountRelProperties = (
        FireworksApiKeyToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksApiKeyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksApiKey)-[:OWNED_BY]->(:FireworksUser)
class FireworksApiKeyToUserRel(CartographyRelSchema):
    """The API key is owned by a user in the same account, matched by email address."""

    target_node_label: str = "FireworksUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "email": PropertyRef("owner_email"),
            "account_id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: FireworksApiKeyToUserRelProperties = (
        FireworksApiKeyToUserRelProperties()
    )


@dataclass(frozen=True)
class FireworksApiKeyToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksApiKey)-[:OWNED_BY]->(:FireworksServiceAccount)
class FireworksApiKeyToServiceAccountRel(CartographyRelSchema):
    """The API key is owned by a service account in the same account, matched by email address."""

    target_node_label: str = "FireworksServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "email": PropertyRef("owner_email"),
            "account_id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: FireworksApiKeyToServiceAccountRelProperties = (
        FireworksApiKeyToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksApiKeySchema(CartographyNodeSchema):
    """An API key that authenticates as a Fireworks AI user or service account.

    Listing every key in the account requires an API key owned by an admin. The
    key value itself is never ingested.
    """

    label: str = "FireworksApiKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: FireworksApiKeyNodeProperties = FireworksApiKeyNodeProperties()
    sub_resource_relationship: FireworksApiKeyToAccountRel = (
        FireworksApiKeyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            FireworksApiKeyToUserRel(),
            FireworksApiKeyToServiceAccountRel(),
        ],
    )
