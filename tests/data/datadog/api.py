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

# Profile and sign-in details that Datadog returns for people. Tests assert
# that none reaches the graph.
PROFILE_ATTRIBUTES = (
    "email",
    "name",
    "handle",
    "title",
    "icon",
    "verified",
    "mfa_enabled",
    "last_login_time",
    "allowed_login_methods",
)
PROFILE_SENTINELS = (
    "Alice Admin",
    "Bob Former",
    "Carol Invited",
    "Staff Engineer",
    "https://secure.gravatar.com/avatar/example",
    "2026-11-01T12:00:00+00:00",
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
        "Access auditor",
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
        "title": "Staff Engineer" if not service_account else None,
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

# Email addresses of people, which must never reach the graph.
HUMAN_EMAILS = tuple(
    user["attributes"]["email"]
    for user in USERS
    if not user["attributes"]["service_account"]
)

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
        {
            "type": "roles",
            "id": AUDITOR_ROLE_ID,
            "attributes": {"name": "Access auditor"},
        },
    ],
}

PAGINATED_PATHS = {
    "/api/v2/roles": ROLES,
    "/api/v2/users": USERS,
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
    """A second organization with one admin."""
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
