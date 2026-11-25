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
from cartography.models.ontology.labels import IDENTITY_PROVIDER


@dataclass(frozen=True)
class FireworksIdentityProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Resource name of the identity provider, such as "
            "`accounts/my-account/identityProviders/okta`."
        ),
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable identity provider name.",
    )
    protocol: PropertyRef = PropertyRef(
        "protocol",
        description="Federation protocol: `SAML` or `OIDC`.",
    )
    issuer: PropertyRef = PropertyRef(
        "issuer",
        description="OIDC issuer URL, or the SAML metadata URL for SAML providers.",
    )
    client_id: PropertyRef = PropertyRef(
        "client_id",
        description="OIDC client ID.",
    )
    saml_email_attribute: PropertyRef = PropertyRef(
        "saml_email_attribute",
        description="SAML attribute that carries the user's email address.",
    )
    tenant_domains: PropertyRef = PropertyRef(
        "tenant_domains",
        description="Email domains that sign in through this identity provider.",
    )
    domain_url: PropertyRef = PropertyRef(
        "domain_url",
        description="Sign-in domain URL.",
    )
    enforce_sso: PropertyRef = PropertyRef(
        "enforce_sso",
        description=(
            "Whether users on the tenant domains must sign in through this provider "
            "and users on other domains are blocked. API keys aren't affected."
        ),
    )
    enable_jit_user_provisioning: PropertyRef = PropertyRef(
        "enable_jit_user_provisioning",
        description="Whether users are created on their first SSO sign-in.",
    )
    jit_default_role: PropertyRef = PropertyRef(
        "jit_default_role",
        description="Role given to users created on their first SSO sign-in.",
    )
    enable_idp_initiated_sso: PropertyRef = PropertyRef(
        "enable_idp_initiated_sso",
        description="Whether users can start SAML sign-in from the identity provider.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Identity provider state, such as `READY`.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="RFC 3339 timestamp when the identity provider was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="RFC 3339 timestamp when the identity provider was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksIdentityProviderToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FireworksAccount)-[:RESOURCE]->(:FireworksIdentityProvider)
class FireworksIdentityProviderToAccountRel(CartographyRelSchema):
    """The account trusts the identity provider for single sign-on."""

    target_node_label: str = "FireworksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FireworksIdentityProviderToAccountRelProperties = (
        FireworksIdentityProviderToAccountRelProperties()
    )


@dataclass(frozen=True)
class FireworksIdentityProviderSchema(CartographyNodeSchema):
    """A custom SAML or OIDC single sign-on (SSO) identity provider for a Fireworks AI account.

    The OIDC client secret and SAML metadata XML are never ingested.
    """

    label: str = "FireworksIdentityProvider"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IDENTITY_PROVIDER])
    properties: FireworksIdentityProviderNodeProperties = (
        FireworksIdentityProviderNodeProperties()
    )
    sub_resource_relationship: FireworksIdentityProviderToAccountRel = (
        FireworksIdentityProviderToAccountRel()
    )
