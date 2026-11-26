import json
from typing import Any
from urllib.parse import urlsplit

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workshop import sync_settings
from cartography.intel.workshop.sync_settings import scoped_id
from cartography.models.workshop.inventory import WorkshopGroupSchema
from cartography.models.workshop.inventory import WorkshopHostSchema
from cartography.models.workshop.inventory import WorkshopUserSchema
from cartography.util import timeit

PAGE_SIZE = 100
MAX_PAGES = 10000
DIRECTORY_TYPES = (
    "DIRECTORY_TYPE_UNSPECIFIED",
    "DIRECTORY_TYPE_DSYNC",
    "DIRECTORY_TYPE_LOCAL",
)


def _field(record: dict[str, Any], camel: str, snake: str) -> Any:
    if camel in record and snake in record:
        raise ValueError("Ambiguous Workshop inventory field aliases")
    return record.get(camel, record.get(snake))


def _string(
    record: dict[str, Any], camel: str, snake: str, required: bool = False
) -> str:
    value = _field(record, camel, snake) if camel != snake else record.get(camel)
    if value is None and not required:
        return ""
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError("Invalid Workshop inventory string")
    return value


def _strings(record: dict[str, Any], camel: str, snake: str) -> list[str]:
    value = _field(record, camel, snake) if camel != snake else record.get(camel)
    if value is None:
        return []
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError("Invalid Workshop inventory string list")
    return list(dict.fromkeys(value))


def _count(value: Any) -> int:
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        value = int(value)
    if type(value) is not int or value < 0:
        raise ValueError("Invalid Workshop host count")
    return value


@timeit
def get(
    api_url: str, api_key: str, method: str, group_id: str | None = None
) -> list[dict[str, Any]]:
    fields = {
        "ListHosts": ("hosts", "uuid"),
        "ListUsers": ("users", "id"),
        "ListTags": ("tags", "tag"),
        "ListGroups": ("groups", "id"),
        "ListGroupMembers": ("members", "id"),
    }
    field, identity = fields[method]
    if method == "ListGroupMembers":
        if not isinstance(group_id, str) or not group_id.strip():
            raise ValueError("Workshop group membership requires a group ID")
    elif group_id is not None:
        raise ValueError("Unexpected Workshop group ID")
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
    result = []
    seen: set[str] = set()
    expected_count = None
    more_expected = False
    for page in range(1, MAX_PAGES + 1):
        response = requests.get(
            f"{api_url.rstrip('/')}/workshop.v1.WorkshopService/{method}",
            headers={"Authorization": api_key},
            params={
                "encoding": "json",
                "message": json.dumps(
                    {
                        "pageSize": PAGE_SIZE,
                        "page": page,
                        **({"groupId": group_id} if group_id is not None else {}),
                    }
                ),
            },
            timeout=(10, 60),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Workshop inventory did not return HTTP 200")
        payload = response.json()
        allowed = {field, "more", "count"} if method == "ListHosts" else {field, "more"}
        if not isinstance(payload, dict) or set(payload) - allowed:
            raise ValueError("Invalid Workshop inventory response")
        batch = payload.get(field, [])
        more = payload.get("more")
        if not isinstance(batch, list) or (
            "more" in payload and type(more) is not bool
        ):
            raise ValueError("Invalid Workshop inventory page")
        if "count" in payload:
            count = _count(payload["count"])
            if expected_count is not None and count != expected_count:
                raise ValueError("Workshop host count changed during pagination")
            expected_count = count
        for item in batch:
            if not isinstance(item, dict):
                raise ValueError("Invalid Workshop inventory record")
            key = _string(item, identity, identity, required=True)
            if key in seen:
                raise ValueError("Repeated Workshop inventory record")
            seen.add(key)
        result.extend(batch)
        if (
            expected_count is not None
            and expected_count <= 10000
            and len(result) > expected_count
        ):
            raise ValueError("Workshop host count does not match returned records")
        if not batch and (more is True or more_expected):
            raise ValueError("Workshop inventory omitted promised records")
        more_expected = more is True
        if more is False or not batch:
            if expected_count is not None and (
                (expected_count <= 10000 and len(result) != expected_count)
                or (expected_count > 10000 and len(result) <= 10000)
            ):
                raise ValueError("Workshop host inventory is incomplete")
            return result
    raise ValueError("Workshop inventory pagination did not terminate")


def _directory_type(record: dict[str, Any]) -> str:
    value = record.get("type", DIRECTORY_TYPES[0])
    if type(value) is int and 0 <= value < len(DIRECTORY_TYPES):
        value = DIRECTORY_TYPES[value]
    if not isinstance(value, str) or value not in DIRECTORY_TYPES:
        raise ValueError("Invalid Workshop directory type")
    return value


def transform_users(
    users: list[dict[str, Any]], tenant_id: str
) -> list[dict[str, Any]]:
    result = []
    for user in users:
        result.append(
            {
                "id": scoped_id(tenant_id, _string(user, "id", "id", required=True)),
                "user_id": user["id"],
                "username": _string(user, "username", "username", required=True),
                "manager_email": _string(user, "managerEmail", "manager_email"),
                "department_name": _string(user, "departmentName", "department_name"),
                "cost_center_name": _string(user, "costCenterName", "cost_center_name"),
                "directory_type": _directory_type(user),
            },
        )
    return result


def transform_groups(
    groups: list[dict[str, Any]],
    members: dict[str, list[dict[str, Any]]],
    users: list[dict[str, Any]],
    tenant_id: str,
) -> list[dict[str, Any]]:
    user_ids = {user["id"] for user in users}
    result = []
    for group in groups:
        group_id = _string(group, "id", "id", required=True)
        member_ids = [
            scoped_id(tenant_id, _string(member, "id", "id", required=True))
            for member in members[group_id]
        ]
        if not set(member_ids) <= user_ids:
            raise ValueError("Workshop group references a user missing from ListUsers")
        managed = _field(group, "tagsManaged", "tags_managed")
        if managed is not None and type(managed) is not bool:
            raise ValueError("Invalid Workshop group tags-managed flag")
        result.append(
            {
                "id": scoped_id(tenant_id, group_id),
                "group_id": group_id,
                "name": _string(group, "name", "name", required=True),
                "description": _string(group, "description", "description"),
                "directory_type": _directory_type(group),
                "idp_id": _string(group, "idpId", "idp_id"),
                "tags_managed": managed if managed is not None else False,
                "tag_ids": [
                    scoped_id(tenant_id, tag) for tag in _strings(group, "tags", "tags")
                ],
                "member_ids": member_ids,
            }
        )
    return result


def _host_tags(host: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(["global", *_strings(host, "tags", "tags")]))


def transform_hosts(
    hosts: list[dict[str, Any]],
    users: list[dict[str, Any]],
    tenant_id: str,
) -> list[dict[str, Any]]:
    by_username: dict[str, list[str]] = {}
    for user in users:
        by_username.setdefault(user["username"], []).append(user["id"])
    result = []
    for host in hosts:
        truncated = _field(host, "tagsTruncated", "tags_truncated")
        if truncated is not None and type(truncated) is not bool:
            raise ValueError("Invalid Workshop tags-truncated flag")
        if truncated:
            raise ValueError("Workshop host tags are truncated")
        uuid = _string(host, "uuid", "uuid", required=True)
        primary_user = _string(host, "primaryUser", "primary_user")
        matches = by_username.get(primary_user, [])
        result.append(
            {
                "id": scoped_id(tenant_id, uuid),
                "uuid": uuid,
                "hostname": _string(host, "hostname", "hostname"),
                "serial": _string(host, "serial", "serial"),
                "machine_model": _string(host, "machineModel", "machine_model"),
                "os_version": _string(host, "osVersion", "os_version"),
                "os_build": _string(host, "osBuild", "os_build"),
                "santa_version": _string(host, "santaVersion", "santa_version"),
                "last_sync": _string(host, "lastSync", "last_sync"),
                "primary_user": primary_user,
                "primary_user_groups": _strings(
                    host, "primaryUserGroups", "primary_user_groups"
                ),
                "primary_user_id": matches[0] if len(matches) == 1 else None,
                "tag_ids": [scoped_id(tenant_id, tag) for tag in _host_tags(host)],
            },
        )
    return result


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    api_key: str,
    tenant_id: str,
    update_tag: int,
) -> None:
    settings = sync_settings.transform(sync_settings.get(api_url, api_key), tenant_id)
    raw_hosts = get(api_url, api_key, "ListHosts")
    users = transform_users(get(api_url, api_key, "ListUsers"), tenant_id)
    catalog = get(api_url, api_key, "ListTags")
    hosts = transform_hosts(raw_hosts, users, tenant_id)
    raw_groups = get(api_url, api_key, "ListGroups")
    members = {
        group["id"]: get(api_url, api_key, "ListGroupMembers", group["id"])
        for group in raw_groups
    }
    groups = transform_groups(raw_groups, members, users, tenant_id)
    tags = {item["tag"]: item for item in settings}
    for tag in (
        [item["tag"] for item in catalog]
        + [tag for host in raw_hosts for tag in _host_tags(host)]
        + [tag for group in raw_groups for tag in _strings(group, "tags", "tags")]
    ):
        tags.setdefault(tag, {"id": scoped_id(tenant_id, tag), "tag": tag})
    sync_settings.load_settings(
        neo4j_session, list(tags.values()), tenant_id, update_tag
    )
    for schema, data in (
        (WorkshopUserSchema(), users),
        (WorkshopGroupSchema(), groups),
        (WorkshopHostSchema(), hosts),
    ):
        load(neo4j_session, schema, data, lastupdated=update_tag, TENANT_ID=tenant_id)
    for schema in (WorkshopHostSchema(), WorkshopGroupSchema(), WorkshopUserSchema()):
        GraphJob.from_node_schema(
            schema, {"UPDATE_TAG": update_tag, "TENANT_ID": tenant_id}
        ).run(neo4j_session)
