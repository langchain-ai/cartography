"""Synthetic Datadog API payloads and an in-memory fake of the Datadog API.

Every value is invented. The shapes follow the Datadog v2 API responses for
the endpoints that the Datadog module reads.
"""

import copy
import json
from typing import Any

import requests

ORG_ID = "00000000-0000-beef-0000-0000000000a1"
OTHER_ORG_ID = "00000000-0000-beef-0000-0000000000b2"

ADMIN_ROLE_ID = "role-admin-0001"
STANDARD_ROLE_ID = "role-standard-0002"
READ_ONLY_ROLE_ID = "role-readonly-0003"
AUDITOR_ROLE_ID = "role-auditor-0004"

ALICE_ID = "user-alice-0001"
BOB_ID = "user-bob-0002"
CAROL_ID = "user-carol-0003"
CI_SA_ID = "sa-ci-0001"
CARTOGRAPHY_SA_ID = "sa-cartography-0002"

# Values that look like secrets. Tests assert that none reaches the graph.
FAKE_SECRETS = (
    "fakeapikeyvalue000000000000000001",
    "fakeappkeyvalue00000000000000000000000001",
    "ddpat_fakepublicportion01",
    "ddpat_fakepublicportion01_fakesecretsecretsecret",
    "ddsat_fakepublicportion02",
)

GENERATED_USER_COUNT = 230


def _permission(permission_id: str, name: str) -> dict[str, Any]:
    return {
        "type": "permissions",
        "id": permission_id,
        "attributes": {
            "name": name,
            "display_name": name.replace("_", " ").title(),
            "group_name": "Access Management",
            "restricted": False,
        },
    }


PERMISSIONS = [
    _permission("perm-0001", "user_access_read"),
    _permission("perm-0002", "user_access_manage"),
    _permission("perm-0003", "api_keys_read"),
    _permission("perm-0004", "api_keys_write"),
    _permission("perm-0005", "org_app_keys_read"),
    _permission("perm-0006", "dashboards_read"),
]


def _role(
    role_id: str,
    name: str,
    permission_ids: list[str],
    user_count: int,
) -> dict[str, Any]:
    return {
        "type": "roles",
        "id": role_id,
        "attributes": {
            "name": name,
            "created_at": "2024-01-01T00:00:00+00:00",
            "modified_at": "2024-06-01T00:00:00+00:00",
            "user_count": user_count,
        },
        "relationships": {
            "permissions": {
                "data": [
                    {"type": "permissions", "id": permission_id}
                    for permission_id in permission_ids
                ],
            },
        },
    }


ROLES = [
    _role(
        ADMIN_ROLE_ID,
        "Datadog Admin Role",
        ["perm-0001", "perm-0002", "perm-0003", "perm-0004", "perm-0005"],
        1,
    ),
    _role(STANDARD_ROLE_ID, "Datadog Standard Role", ["perm-0001", "perm-0006"], 2),
    _role(READ_ONLY_ROLE_ID, "Datadog Read Only Role", ["perm-0001"], 230),
    # perm-9999 is missing from PERMISSIONS on purpose.
    _role(
        AUDITOR_ROLE_ID,
        "Key auditor",
        ["perm-0001", "perm-0003", "perm-0005", "perm-9999"],
        1,
    ),
]


def _user(
    user_id: str,
    name: str,
    email: str,
    role_ids: list[str],
    *,
    service_account: bool = False,
    status: str = "Active",
    mfa_enabled: bool | None = None,
    org_id: str = ORG_ID,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {
        "name": name,
        "handle": email,
        "email": email,
        "created_at": "2024-02-01T00:00:00+00:00",
        "modified_at": "2024-07-01T00:00:00+00:00",
        "icon": "https://secure.gravatar.com/avatar/example",
        "title": None,
        "verified": status != "Pending",
        "service_account": service_account,
        "disabled": status == "Disabled",
        "allowed_login_methods": [],
        "status": status,
    }
    if mfa_enabled is not None:
        attributes["mfa_enabled"] = mfa_enabled
        attributes["last_login_time"] = "2026-11-01T12:00:00+00:00"
    return {
        "type": "users",
        "id": user_id,
        "attributes": attributes,
        "relationships": {
            "roles": {"data": [{"type": "roles", "id": rid} for rid in role_ids]},
            "org": {"data": {"type": "orgs", "id": org_id}},
        },
    }


NAMED_USERS = [
    _user(
        ALICE_ID,
        "Alice Admin",
        "alice@example.com",
        [ADMIN_ROLE_ID, READ_ONLY_ROLE_ID],
        mfa_enabled=True,
    ),
    _user(
        BOB_ID,
        "Bob Former",
        "bob@example.com",
        [STANDARD_ROLE_ID],
        status="Disabled",
        mfa_enabled=False,
    ),
    _user(CAROL_ID, "Carol Invited", "carol@example.com", [], status="Pending"),
    _user(
        CI_SA_ID,
        "ci-deployer",
        "ci-deployer@example.com",
        [STANDARD_ROLE_ID],
        service_account=True,
    ),
    _user(
        CARTOGRAPHY_SA_ID,
        "cartography-readonly",
        "security@example.com",
        [AUDITOR_ROLE_ID],
        service_account=True,
    ),
]

# Enough filler users that the listing spans three pages of 100.
GENERATED_USERS = [
    _user(
        f"user-gen-{index:04d}",
        f"Generated User {index}",
        f"user{index:04d}@example.com",
        [READ_ONLY_ROLE_ID],
    )
    for index in range(GENERATED_USER_COUNT)
]

USERS = NAMED_USERS + GENERATED_USERS

CURRENT_USER = {
    "data": copy.deepcopy(NAMED_USERS[4]),
    "included": [
        {
            "type": "orgs",
            "id": ORG_ID,
            "attributes": {
                "name": "Example Corp",
                "public_id": "abc123def",
                "created_at": "2020-01-01T00:00:00+00:00",
            },
        },
        {"type": "roles", "id": AUDITOR_ROLE_ID, "attributes": {"name": "Key auditor"}},
    ],
}

API_KEYS = [
    {
        "type": "api_keys",
        "id": "apikey-0001",
        "attributes": {
            "name": "production-agents",
            # List responses never include `key`; this checks that transforms
            # drop it anyway.
            "key": FAKE_SECRETS[0],
            "last4": "0001",
            "category": "default",
            "created_at": "2023-03-01T00:00:00+00:00",
            "modified_at": "2023-03-01T00:00:00+00:00",
            "date_last_used": "2026-11-20T00:00:00+00:00",
            "remote_config_read_enabled": True,
        },
        "relationships": {
            "created_by": {"data": {"type": "users", "id": BOB_ID}},
            "modified_by": {"data": {"type": "users", "id": BOB_ID}},
            "leak_information": {"data": None},
        },
    },
    {
        "type": "api_keys",
        "id": "apikey-0002",
        "attributes": {
            "name": "ci-metrics",
            "last4": "0002",
            "category": "default",
            "created_at": "2024-03-01T00:00:00+00:00",
            "modified_at": "2024-03-01T00:00:00+00:00",
            "date_last_used": None,
            "remote_config_read_enabled": False,
        },
        "relationships": {
            "created_by": {"data": {"type": "users", "id": CI_SA_ID}},
            "modified_by": {"data": None},
            "leak_information": {
                "data": {"type": "leaked_keys", "id": "leak-0001"},
            },
        },
    },
]

APPLICATION_KEYS = [
    {
        "type": "application_keys",
        "id": "appkey-0001",
        "attributes": {
            "name": "alice-laptop",
            "key": FAKE_SECRETS[1],
            "last4": "a001",
            "created_at": "2023-05-01T00:00:00+00:00",
            "last_used_at": "2026-10-01T00:00:00+00:00",
            "scopes": None,
        },
        "relationships": {
            "owned_by": {"data": {"type": "users", "id": ALICE_ID}},
            "leak_information": {"data": None},
        },
    },
    {
        "type": "application_keys",
        "id": "appkey-0002",
        "attributes": {
            "name": "cartography",
            "last4": "a002",
            "created_at": "2026-01-01T00:00:00+00:00",
            "last_used_at": "2026-11-25T00:00:00+00:00",
            "scopes": ["user_access_read", "org_app_keys_read", "api_keys_read"],
        },
        "relationships": {
            "owned_by": {"data": {"type": "users", "id": CARTOGRAPHY_SA_ID}},
            "leak_information": {"data": None},
        },
    },
    {
        "type": "application_keys",
        "id": "appkey-0003",
        "attributes": {
            "name": "bob-old-script",
            "last4": "a003",
            "created_at": "2022-01-01T00:00:00+00:00",
            "last_used_at": None,
            "scopes": [],
        },
        "relationships": {
            "owned_by": {"data": {"type": "users", "id": BOB_ID}},
        },
    },
]

ACCESS_TOKENS = [
    {
        "type": "personal_access_tokens",
        "id": "pat-0001",
        "attributes": {
            "name": "alice-cli",
            "public_portion": FAKE_SECRETS[2],
            "key": FAKE_SECRETS[3],
            "created_at": "2026-11-01T00:00:00+00:00",
            "modified_at": None,
            "expires_at": "2026-12-01T00:00:00+00:00",
            "last_used_at": "2026-11-24T00:00:00+00:00",
            "scopes": ["dashboards_read"],
        },
        "relationships": {
            "owned_by": {"data": {"type": "users", "id": ALICE_ID}},
            "leak_information": {"data": None},
        },
    },
    {
        "type": "service_access_tokens",
        "id": "sat-0001",
        "attributes": {
            "name": "ci-deployer-token",
            "public_portion": FAKE_SECRETS[4],
            "created_at": "2026-06-01T00:00:00+00:00",
            "modified_at": "2026-06-02T00:00:00+00:00",
            "expires_at": None,
            "last_used_at": "2026-11-25T00:00:00+00:00",
            "scopes": ["monitors_write", "dashboards_read"],
        },
        "relationships": {
            "owned_by": {"data": {"type": "users", "id": CI_SA_ID}},
        },
    },
]

PAGINATED_PATHS = {
    "/api/v2/roles": ROLES,
    "/api/v2/users": USERS,
    "/api/v2/api_keys": API_KEYS,
    "/api/v2/application_keys": APPLICATION_KEYS,
    "/api/v2/personal_access_tokens": ACCESS_TOKENS,
}

OBJECT_PATHS: dict[str, Any] = {
    "/api/v2/current_user": CURRENT_USER,
    "/api/v2/permissions": {"data": PERMISSIONS},
}


def _response(url: str, status_code: int, body: Any) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    response.reason = "OK" if status_code < 400 else "Error"
    response._content = json.dumps(body).encode()
    return response


class FakeDatadogAPI:
    """An in-memory stand-in for a Datadog API session.

    Pass `failures` to answer `(path, page_number)` with an HTTP status code
    (use page number 0 for unpaginated paths), `total_overrides` to report a
    wrong `meta.page.total_filtered_count`, `omit_totals` to drop `meta`, and
    `duplicate_pages` to repeat the previous page's first item on a page.
    """

    base_url = "https://api.datadoghq.com"

    def __init__(
        self,
        paginated: dict[str, list[dict[str, Any]]] | None = None,
        objects: dict[str, Any] | None = None,
        failures: dict[tuple[str, int], int] | None = None,
        total_overrides: dict[str, int] | None = None,
        omit_totals: set[str] | None = None,
        duplicate_pages: set[tuple[str, int]] | None = None,
    ) -> None:
        self.paginated = copy.deepcopy(
            paginated if paginated is not None else PAGINATED_PATHS
        )
        self.objects = copy.deepcopy(objects if objects is not None else OBJECT_PATHS)
        self.failures = failures or {}
        self.total_overrides = total_overrides or {}
        self.omit_totals = omit_totals or set()
        self.duplicate_pages = duplicate_pages or set()
        self.requests: list[tuple[str, str, dict[str, Any]]] = []

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: Any = None,
    ) -> requests.Response:
        params = dict(params or {})
        self.requests.append(("GET", url, params))
        assert url.startswith(self.base_url), url
        path = url[len(self.base_url) :]
        page_number = int(params.get("page[number]", 0))
        status = self.failures.get((path, page_number))
        if status is not None:
            return _response(url, status, {"errors": ["synthetic failure"]})
        if path in self.objects:
            return _response(url, 200, self.objects[path])
        if path not in self.paginated:
            return _response(url, 404, {"errors": ["Not found"]})
        items = self.paginated[path]
        page_size = int(params.get("page[size]", 10))
        start = page_number * page_size
        page = items[start : start + page_size]
        if (path, page_number) in self.duplicate_pages:
            page = [items[start - page_size]] + page[1:]
        body: dict[str, Any] = {"data": page}
        if path not in self.omit_totals:
            total = self.total_overrides.get(path, len(items))
            body["meta"] = {
                "page": {"total_count": total, "total_filtered_count": total}
            }
        return _response(url, 200, body)

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        if method.upper() != "GET":
            raise AssertionError(f"Datadog module sent a {method} request to {url}")
        return self.get(url, kwargs.get("params"), kwargs.get("timeout"))


def other_org_api() -> FakeDatadogAPI:
    """A second organization with one admin and no keys."""
    admin = _user(
        "user-other-0001",
        "Other Admin",
        "admin@other.example",
        ["role-other-admin"],
        org_id=OTHER_ORG_ID,
    )
    return FakeDatadogAPI(
        paginated={
            "/api/v2/roles": [_role("role-other-admin", "Datadog Admin Role", [], 1)],
            "/api/v2/users": [admin],
            "/api/v2/api_keys": [],
            "/api/v2/application_keys": [],
            "/api/v2/personal_access_tokens": [],
        },
        objects={
            "/api/v2/current_user": {
                "data": admin,
                "included": [
                    {
                        "type": "orgs",
                        "id": OTHER_ORG_ID,
                        "attributes": {"name": "Other Corp", "public_id": "zzz999"},
                    },
                ],
            },
            "/api/v2/permissions": {"data": PERMISSIONS},
        },
    )
