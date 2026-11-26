import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
TIMEOUT = (60, 60)

DEFAULT_SITE = "datadoghq.com"
PAGE_SIZE = 100
MAX_PAGES = 10_000
LIST_ATTEMPTS = 3


class DatadogIncompleteListError(Exception):
    """A Datadog listing can't be proven complete, so it must not drive cleanup."""


class ReadOnlySession(requests.Session):
    """A `requests.Session` that refuses every method except `GET`."""

    def request(
        self,
        method: str | bytes,
        url: str | bytes,
        *args: Any,
        **kwargs: Any,
    ) -> requests.Response:
        normalized = method.decode() if isinstance(method, bytes) else method
        if normalized.upper() != "GET":
            raise PermissionError(
                f"The Datadog module is read-only and refused a {normalized} request.",
            )
        return super().request(method, url, *args, **kwargs)


def build_base_url(site: str | None) -> str:
    """Return the Datadog API base URL for a site such as `datadoghq.eu`.

    A value that starts with `https://` is used as the base URL as is.
    """
    value = (site or DEFAULT_SITE).strip().rstrip("/")
    if value.startswith("https://"):
        return value
    if "://" in value:
        raise ValueError(f"Datadog site must use HTTPS: {value}")
    return f"https://api.{value}"


def build_session(api_key: str | None, app_key: str) -> ReadOnlySession:
    session = ReadOnlySession()
    # Datadog answers 429 when a rate limit is hit. Retry with backoff on
    # throttling and transient server errors, for GET requests only.
    retry_policy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    headers = {
        "Accept": "application/json",
        "DD-APPLICATION-KEY": app_key,
    }
    # Service access tokens authenticate on their own; application keys also
    # need an API key.
    if api_key:
        headers["DD-API-KEY"] = api_key
    session.headers.update(headers)
    return session


def get_object(
    api_session: requests.Session,
    base_url: str,
    path: str,
) -> dict[str, Any]:
    response = api_session.get(f"{base_url}{path}", timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _total_count(body: dict[str, Any]) -> int | None:
    page = (body.get("meta") or {}).get("page") or {}
    total = page.get("total_filtered_count")
    if total is None:
        total = page.get("total_count")
    return total


def _list_once(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    expected_total: int | None = None
    for page_number in range(MAX_PAGES):
        page_params = {
            **params,
            "page[size]": PAGE_SIZE,
            "page[number]": page_number,
        }
        response = api_session.get(url, params=page_params, timeout=TIMEOUT)
        response.raise_for_status()
        body = response.json()
        items = body["data"]
        total = _total_count(body)
        if page_number == 0:
            expected_total = total
        elif total != expected_total:
            raise DatadogIncompleteListError(
                f"Datadog changed the total for {url} from {expected_total} to "
                f"{total} while Cartography was paging through it.",
            )
        for item in items:
            if item["id"] in seen_ids:
                raise DatadogIncompleteListError(
                    f"Datadog returned {url} item {item['id']} on more than one page.",
                )
            seen_ids.add(item["id"])
            results.append(item)

        if expected_total is None:
            if len(items) < PAGE_SIZE:
                return results
            continue
        if len(results) == expected_total:
            return results
        if len(results) > expected_total or not items:
            raise DatadogIncompleteListError(
                f"Datadog returned {len(results)} items for {url}, but reported "
                f"a total of {expected_total}.",
            )
    raise DatadogIncompleteListError(
        f"Datadog returned more than {MAX_PAGES} pages for {url}.",
    )


def paginated_get(
    api_session: requests.Session,
    base_url: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch every page of a Datadog v2 list endpoint.

    Datadog pages with `page[size]` and `page[number]` and reports the total in
    `meta.page`. Cartography only returns a listing that it can prove complete:
    every page must report the same total, no item may appear twice, and the
    number of items must match the total. Otherwise, the listing is retried and
    then raises `DatadogIncompleteListError`, so a sync never cleans up nodes
    from a partial listing. HTTP errors propagate unchanged.
    """
    url = f"{base_url}{path}"
    for attempt in range(1, LIST_ATTEMPTS + 1):
        try:
            return _list_once(api_session, url, dict(params or {}))
        except DatadogIncompleteListError:
            if attempt == LIST_ATTEMPTS:
                raise
            logger.warning(
                "Datadog listing %s changed during pagination; retrying (%d/%d).",
                url,
                attempt,
                LIST_ATTEMPTS,
            )
    raise AssertionError("unreachable")


def relationship_id(item: dict[str, Any], name: str) -> str | None:
    data = ((item.get("relationships") or {}).get(name) or {}).get("data")
    if not data:
        return None
    return data["id"]


def relationship_ids(item: dict[str, Any], name: str) -> list[str]:
    data = ((item.get("relationships") or {}).get(name) or {}).get("data") or []
    return sorted({entry["id"] for entry in data})
