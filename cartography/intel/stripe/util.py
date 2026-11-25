from typing import Any
from urllib.parse import parse_qs
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

STRIPE_API_BASE_URL = "https://api.stripe.com"
STRIPE_API_VERSION = "2026-11-18.endive"
TIMEOUT = (60, 60)
PAGE_LIMIT = 100


def build_session(api_key: str) -> requests.Session:
    session = requests.Session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update(
        {
            "Authorization": f"Bearer {api_key}",
            "Stripe-Version": STRIPE_API_VERSION,
        },
    )
    return session


def get_object(api_session: requests.Session, path: str) -> dict[str, Any]:
    response = api_session.get(f"{STRIPE_API_BASE_URL}{path}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def list_v1(
    api_session: requests.Session,
    path: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """List every object of a /v1 list endpoint, following `starting_after` cursors."""
    results: list[dict[str, Any]] = []
    query: dict[str, Any] = {**(params or {}), "limit": PAGE_LIMIT}
    while True:
        response = api_session.get(
            f"{STRIPE_API_BASE_URL}{path}",
            params=query,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        page = response.json()
        data = page["data"]
        results.extend(data)
        if not page["has_more"] or not data:
            return results
        query["starting_after"] = data[-1]["id"]


def list_v2(
    api_session: requests.Session,
    path: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """List every object of a /v2 list endpoint, following its `page` tokens."""
    results: list[dict[str, Any]] = []
    query: dict[str, Any] = {**(params or {}), "limit": PAGE_LIMIT}
    while True:
        response = api_session.get(
            f"{STRIPE_API_BASE_URL}{path}",
            params=query,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        page = response.json()
        results.extend(page["data"])
        next_page_url = page.get("next_page_url")
        if not next_page_url:
            return results
        query["page"] = parse_qs(urlsplit(next_page_url).query)["page"][0]


def is_permission_error(error: requests.HTTPError) -> bool:
    """Report whether Stripe refused a request because the key lacks a permission."""
    return error.response is not None and error.response.status_code == 403


def sanitize_url(url: str | None) -> tuple[str | None, str | None]:
    """Return the URL without credentials, query string, or fragment, and its host."""
    if not url:
        return None, None
    parts = urlsplit(url)
    host = parts.hostname
    netloc = host or ""
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, "", "")), host
