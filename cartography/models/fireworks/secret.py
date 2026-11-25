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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class FireworksSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Resource name of the secret, such as `accounts/my-account/secrets/my-secret`.",
    )
    key_name: PropertyRef = PropertyRef(
        "key_name",
        description="Name of the secret's key, such as `WOLFRAM_ALPHA_API_KEY`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksSecretToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksSecret)
class FireworksSecretToAccountRel(CartographyRelSchema):
    """The account contains the secret."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksSecretToAccountRelProperties = (
        FireworksSecretToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksSecretSchema(CartographyNodeSchema):
    """A secret stored in a Fireworks AI account, such as a credential that evaluators use.

    The API never returns the secret value, so Cartography records only its names.
    """

    label: str = "FireworksSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    properties: FireworksSecretNodeProperties = FireworksSecretNodeProperties()
    sub_resource_relationship: FireworksSecretToAccountRel = (
        FireworksSecretToAccountRel()
    )
