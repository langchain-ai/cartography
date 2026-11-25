import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.stripe.util import get_object
from cartography.models.stripe.account import StripeAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    update_tag: int,
) -> str:
    """Sync the account that owns the API key, and return its ID."""
    raw_account = get(api_session)
    account = transform(raw_account)
    load_account(neo4j_session, account, update_tag)
    return account["id"]


@timeit
def get(api_session: requests.Session) -> dict[str, Any]:
    return get_object(api_session, "/v1/account")


def transform_account_fields(account: dict[str, Any]) -> dict[str, Any]:
    """Pick the account fields that both the account and connected accounts store."""
    business_profile = account.get("business_profile") or {}
    settings = account.get("settings") or {}
    dashboard = settings.get("dashboard") or {}
    requirements = account.get("requirements") or {}
    controller = account.get("controller") or {}
    capabilities = account.get("capabilities") or {}
    return {
        "id": account["id"],
        "name": business_profile.get("name"),
        "display_name": dashboard.get("display_name"),
        "url": business_profile.get("url"),
        "mcc": business_profile.get("mcc"),
        "country": account.get("country"),
        "default_currency": account.get("default_currency"),
        "type": account.get("type"),
        "business_type": account.get("business_type"),
        "controller_type": controller.get("type"),
        "charges_enabled": account.get("charges_enabled"),
        "payouts_enabled": account.get("payouts_enabled"),
        "details_submitted": account.get("details_submitted"),
        "disabled_reason": requirements.get("disabled_reason"),
        "active_capabilities": sorted(
            name for name, status in capabilities.items() if status == "active"
        ),
        "created": account.get("created"),
    }


def transform(account: dict[str, Any]) -> dict[str, Any]:
    settings = account.get("settings") or {}
    decline_on = (settings.get("card_payments") or {}).get("decline_on") or {}
    result = transform_account_fields(account)
    result["name"] = result["name"] or result["display_name"] or result["id"]
    result["email"] = account.get("email")
    result["decline_on_avs_failure"] = decline_on.get("avs_failure")
    result["decline_on_cvc_failure"] = decline_on.get("cvc_failure")
    result["timezone"] = (settings.get("dashboard") or {}).get("timezone")
    return result


@timeit
def load_account(
    neo4j_session: neo4j.Session,
    account: dict[str, Any],
    update_tag: int,
) -> None:
    load(neo4j_session, StripeAccountSchema(), [account], lastupdated=update_tag)
