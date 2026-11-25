from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class BasetenOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("org_id", description="Baseten organization ID.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the organization.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the organization was created.",
    )
    allow_personal_api_keys: PropertyRef = PropertyRef(
        "allow_personal_api_keys",
        description=(
            "Whether members can create new personal API keys. Existing keys keep "
            "working when this is `false`."
        ),
    )
    allow_service_account_api_keys: PropertyRef = PropertyRef(
        "allow_service_account_api_keys",
        description=(
            "Whether new team and organization API keys can be created. Existing keys "
            "keep working when this is `false`."
        ),
    )
    allow_team_admins_to_manage_roles: PropertyRef = PropertyRef(
        "allow_team_admins_to_manage_roles",
        description=(
            "Whether team admins can create, change, and delete their team's custom "
            "roles. Null when custom roles aren't available to the organization or the "
            "API key can't read its roles."
        ),
    )
    aws_assume_role_enabled: PropertyRef = PropertyRef(
        "aws_assume_role_enabled",
        description=(
            "Whether AWS AssumeRole authentication is enabled, so Baseten can assume an "
            "IAM role in your AWS accounts."
        ),
    )
    aws_assume_role_baseten_role_arn: PropertyRef = PropertyRef(
        "aws_assume_role_baseten_role_arn",
        description=(
            "ARN of the Baseten-owned IAM role to allow in your IAM role's trust "
            "policy when AWS AssumeRole authentication is enabled."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenOrganizationSchema(CartographyNodeSchema):
    """
    A Baseten organization, the tenant that owns teams, users, API keys, secrets,
    models, and Chains.

    Cartography reads the organization of the configured API key from
    `GET /v1/organizations/me`, together with its API key creation controls.
    """

    label: str = "BasetenOrganization"
    properties: BasetenOrganizationNodeProperties = BasetenOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
