from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class FireworksAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Fireworks AI account ID, such as `my-account`.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Resource name of the account, such as `accounts/my-account`.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable account name.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="Primary email address for billing invoices and account notifications.",
    )
    account_type: PropertyRef = PropertyRef(
        "account_type",
        description="Account type, such as `ENTERPRISE`.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Account state, such as `READY`.",
    )
    suspend_state: PropertyRef = PropertyRef(
        "suspend_state",
        description=(
            "Suspension state: `UNSUSPENDED`, `FAILED_PAYMENTS`, `CREDIT_DEPLETED`, "
            "`MONTHLY_SPEND_LIMIT_EXCEEDED`, or `BLOCKED_BY_ABUSE_RULE`."
        ),
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="RFC 3339 timestamp when the account was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="RFC 3339 timestamp when the account was last updated.",
    )
    policy_settings_readable: PropertyRef = PropertyRef(
        "policy_settings_readable",
        description=(
            "Whether Cartography could read the account policy settings. When `false`, "
            "every policy property on this node is null."
        ),
    )
    residency: PropertyRef = PropertyRef(
        "residency",
        description=(
            "Data residency restriction, such as `US` or `EUROPE`. Null when serving "
            "is unrestricted."
        ),
    )
    cmek_required: PropertyRef = PropertyRef(
        "cmek_required",
        description="Whether new customer-data resources must be encrypted with a customer-managed key.",
    )
    zdr_default_enforced: PropertyRef = PropertyRef(
        "zdr_default_enforced",
        description="Zero Data Retention default policy for inference and training.",
    )
    zdr_inference_enforcement: PropertyRef = PropertyRef(
        "zdr_inference_enforcement",
        description=(
            "Zero Data Retention override for inference: `ENFORCED`, `NOT_ENFORCED`, "
            "or null to inherit the default."
        ),
    )
    zdr_training_enforcement: PropertyRef = PropertyRef(
        "zdr_training_enforcement",
        description=(
            "Zero Data Retention override for training: `ENFORCED`, `NOT_ENFORCED`, "
            "or null to inherit the default."
        ),
    )
    zdr_inference_enforced: PropertyRef = PropertyRef(
        "zdr_inference_enforced",
        description="Whether Zero Data Retention is in effect for inference, after inheritance.",
    )
    zdr_training_enforced: PropertyRef = PropertyRef(
        "zdr_training_enforced",
        description="Whether Zero Data Retention is in effect for training, after inheritance.",
    )
    default_allow_serverless: PropertyRef = PropertyRef(
        "default_allow_serverless",
        description="Model access policy default for serverless inference.",
    )
    default_allow_serverless_fast: PropertyRef = PropertyRef(
        "default_allow_serverless_fast",
        description="Model access policy default for serverless Fast mode.",
    )
    default_allow_dedicated_deployments: PropertyRef = PropertyRef(
        "default_allow_dedicated_deployments",
        description="Model access policy default for dedicated deployments.",
    )
    default_allow_training: PropertyRef = PropertyRef(
        "default_allow_training",
        description="Model access policy default for training.",
    )
    model_access_rule_count: PropertyRef = PropertyRef(
        "model_access_rule_count",
        description="Number of per-model access rules that override the defaults.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class FireworksAccountSchema(CartographyNodeSchema):
    """A Fireworks AI account, the tenant that owns users, keys, and serving resources.

    Policy properties come from the account's policy settings, which hold the model
    access policy, data residency, Zero Data Retention (ZDR), and CMEK requirement.
    An account that has never saved policy settings gets the documented defaults:
    every model allowed, no residency restriction, and ZDR off.
    """

    label: str = "FireworksAccount"
    properties: FireworksAccountNodeProperties = FireworksAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
