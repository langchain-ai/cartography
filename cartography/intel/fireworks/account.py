import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.fireworks.util import TIMEOUT
from cartography.models.fireworks.account import FireworksAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ZDR_ENFORCEMENT = {"ENFORCED": True, "NOT_ENFORCED": False}
_MODEL_PERMISSIONS = {
    "default_allow_serverless": "allowServerless",
    "default_allow_serverless_fast": "allowServerlessFast",
    "default_allow_dedicated_deployments": "allowDedicatedDeployments",
    "default_allow_training": "allowTraining",
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    base_url = common_job_parameters["BASE_URL"]
    account = get(api_session, base_url, account_id)
    policy_settings, readable = get_policy_settings(api_session, base_url, account_id)
    data = transform(account, policy_settings, readable, account_id)
    load_account(neo4j_session, data, common_job_parameters["UPDATE_TAG"])


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
) -> dict[str, Any]:
    response = api_session.get(f"{base_url}/accounts/{account_id}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


@timeit
def get_policy_settings(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
) -> tuple[dict[str, Any], bool]:
    """Return the account's policy settings and whether they could be read.

    An account that has never saved policy settings returns 404, which means no
    policy is set. Any account member can read the settings, so a 403 is logged
    and the policy properties stay null.
    """
    response = api_session.get(
        f"{base_url}/accounts/{account_id}/policySettings",
        timeout=TIMEOUT,
    )
    if response.status_code == 404:
        return {}, True
    if response.status_code == 403:
        logger.warning(
            "Fireworks AI API key cannot read policy settings for account %s; "
            "skipping policy properties.",
            account_id,
        )
        return {}, False
    response.raise_for_status()
    return response.json(), True


def transform(
    account: dict[str, Any],
    policy_settings: dict[str, Any],
    policy_settings_readable: bool,
    account_id: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": account_id,
        "name": account.get("name"),
        "display_name": account.get("displayName"),
        "email": account.get("email"),
        "account_type": account.get("accountType"),
        "state": account.get("state"),
        "suspend_state": account.get("suspendState"),
        "create_time": account.get("createTime"),
        "update_time": account.get("updateTime"),
        "policy_settings_readable": policy_settings_readable,
    }
    if policy_settings_readable:
        result.update(_transform_policy_settings(policy_settings))
    return result


def _transform_policy_settings(policy_settings: dict[str, Any]) -> dict[str, Any]:
    zdr = policy_settings.get("zeroDataRetention") or {}
    zdr_default = bool(zdr.get("defaultEnforced", False))
    inference = (zdr.get("inference") or {}).get("enforcement") or ""
    training = (zdr.get("training") or {}).get("enforcement") or ""
    default_permissions = policy_settings.get("defaultPermissions")
    result: dict[str, Any] = {
        "residency": policy_settings.get("residency"),
        "cmek_required": bool(policy_settings.get("cmekRequired", False)),
        "zdr_default_enforced": zdr_default,
        "zdr_inference_enforcement": _explicit_enforcement(inference),
        "zdr_training_enforcement": _explicit_enforcement(training),
        "zdr_inference_enforced": _ZDR_ENFORCEMENT.get(inference, zdr_default),
        "zdr_training_enforced": _ZDR_ENFORCEMENT.get(training, zdr_default),
        "model_access_rule_count": len(policy_settings.get("rules") or []),
    }
    for field, api_field in _MODEL_PERMISSIONS.items():
        # An account without default permissions allows every model.
        result[field] = (
            True if default_permissions is None else default_permissions.get(api_field)
        )
    return result


def _explicit_enforcement(enforcement: str) -> str | None:
    return enforcement if enforcement in _ZDR_ENFORCEMENT else None


@timeit
def load_account(
    neo4j_session: neo4j.Session,
    data: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksAccountSchema(),
        [data],
        lastupdated=update_tag,
    )
