import json
from typing import Any
from urllib.parse import urlsplit

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.workshop.settings import WorkshopClientModeSchema
from cartography.models.workshop.settings import WorkshopTagSchema
from cartography.models.workshop.settings import WorkshopTenantSchema
from cartography.util import timeit

PAGE_SIZE = 100
MAX_PAGES = 10000
CLIENT_MODES = ("UNKNOWN_CLIENT_MODE", "MONITOR", "LOCKDOWN", "STANDALONE")


def scoped_id(tenant_id: str, value: str) -> str:
    return json.dumps([tenant_id, value], separators=(",", ":"))


def _mode(setting: dict[str, Any]) -> str:
    if "clientMode" in setting and "client_mode" in setting:
        raise ValueError("Ambiguous Workshop client mode fields")
    mode = setting.get("clientMode", setting.get("client_mode", "UNKNOWN_CLIENT_MODE"))
    if type(mode) is int and 0 <= mode < len(CLIENT_MODES):
        return CLIENT_MODES[mode]
    if isinstance(mode, str) and mode in CLIENT_MODES:
        return mode
    raise ValueError("Invalid Workshop configured client mode")


def transform(settings: list[dict[str, Any]], tenant_id: str) -> list[dict[str, Any]]:
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise ValueError("Workshop tenant ID must be nonempty")
    result = []
    seen = set()
    for setting in settings:
        if not isinstance(setting, dict):
            raise ValueError("Invalid Workshop sync setting")
        tag = setting.get("tag")
        if not isinstance(tag, str) or not tag.strip() or tag in seen:
            raise ValueError("Missing or duplicate Workshop sync setting tag")
        seen.add(tag)
        mode = _mode(setting)
        result.append(
            {
                "id": scoped_id(tenant_id, tag),
                "tag": tag,
                "mode_id": scoped_id(tenant_id, mode),
                "configured_client_mode": mode,
            },
        )
    return result


@timeit
def get(api_url: str, api_key: str) -> list[dict[str, Any]]:
    parsed = urlsplit(api_url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Workshop API URL must be an HTTPS origin")
    settings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, MAX_PAGES + 1):
        response = requests.get(
            f"{api_url.rstrip('/')}/workshop.v1.WorkshopService/ListSyncSettings",
            headers={"Authorization": api_key},
            params={
                "encoding": "json",
                "message": json.dumps({"pageSize": PAGE_SIZE, "page": page}),
            },
            timeout=(10, 60),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Workshop ListSyncSettings did not return HTTP 200")
        payload = response.json()
        if not isinstance(payload, dict) or set(payload) - {
            "syncSettings",
            "sync_settings",
        }:
            raise ValueError("Invalid Workshop ListSyncSettings response")
        if "syncSettings" in payload and "sync_settings" in payload:
            raise ValueError("Ambiguous Workshop sync settings fields")
        batch = payload.get("syncSettings", payload.get("sync_settings", []))
        if not isinstance(batch, list):
            raise ValueError("Invalid Workshop sync settings page")
        if not batch:
            return settings
        validated = transform(batch, "validation")
        for setting in validated:
            if setting["tag"] in seen:
                raise ValueError("Repeated Workshop sync setting across pages")
            seen.add(setting["tag"])
        settings.extend(batch)
    raise ValueError("Workshop pagination did not reach an empty terminal page")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    api_key: str,
    tenant_id: str,
    update_tag: int,
) -> None:
    tags = transform(get(api_url, api_key), tenant_id)
    modes = [
        {"id": tag["mode_id"], "name": tag["configured_client_mode"]} for tag in tags
    ]
    load(
        neo4j_session,
        WorkshopTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
    for schema, data in (
        (WorkshopClientModeSchema(), modes),
        (WorkshopTagSchema(), tags),
    ):
        load(
            neo4j_session,
            schema,
            data,
            lastupdated=update_tag,
            TENANT_ID=tenant_id,
        )
    parameters = {"UPDATE_TAG": update_tag, "TENANT_ID": tenant_id}
    for schema in (WorkshopTagSchema(), WorkshopClientModeSchema()):
        GraphJob.from_node_schema(schema, parameters).run(neo4j_session)
