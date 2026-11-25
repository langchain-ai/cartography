import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.anthropic.util import TIMEOUT
from cartography.models.anthropic.organization import AnthropicOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Maps Compliance API setting names to AnthropicOrganization properties.
SETTINGS = {
    "api_zero_data_retention_enabled": "api_zero_data_retention_enabled",
    "claude_enterprise_claude_code_zero_data_retention_enabled": (
        "claude_code_zero_data_retention_enabled"
    ),
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    update_tag: int,
) -> None:
    organizations = []
    for org in get_organizations(api_session, base_url):
        settings = get_settings(api_session, base_url, org["uuid"])
        if settings is None:
            continue
        organizations.append(transform(org["uuid"], settings))
    load_organizations(neo4j_session, organizations, update_tag)


@timeit
def get_organizations(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    organizations: list[dict[str, Any]] = []
    params: dict[str, str] = {}
    while True:
        response = api_session.get(
            f"{base_url}/compliance/organizations",
            params=params,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        body = response.json()
        organizations.extend(body.get("data", []))
        if not body.get("has_more") or not body.get("next_page"):
            return organizations
        params = {"page": body["next_page"]}


@timeit
def get_settings(
    api_session: requests.Session,
    base_url: str,
    org_uuid: str,
) -> list[dict[str, Any]] | None:
    response = api_session.get(
        f"{base_url}/compliance/organizations/{org_uuid}/settings",
        timeout=TIMEOUT,
    )
    if response.status_code == 404:
        logger.warning(
            "Anthropic organization settings are not available for %s; skipping.",
            org_uuid,
        )
        return None
    response.raise_for_status()
    return response.json().get("settings", [])


def transform(org_uuid: str, settings: list[dict[str, Any]]) -> dict[str, Any]:
    organization: dict[str, Any] = {"id": org_uuid}
    organization.update({prop: None for prop in SETTINGS.values()})
    for setting in settings:
        prop = SETTINGS.get(setting.get("name", ""))
        if prop:
            organization[prop] = setting.get("value")
    return organization


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )
