from typing import Any

import requests

BASE_URL = "https://api.fireworks.ai/v1"
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
TIMEOUT = (60, 60)
# Fireworks AI coerces any larger page size to 200.
PAGE_SIZE = 200


def paginated_get(
    api_session: requests.Session,
    url: str,
    items_key: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Read every page of a Fireworks AI list endpoint.

    Fireworks AI follows Google AIP-158 pagination: each response carries a
    `nextPageToken` until the last page, which omits it.
    """
    results: list[dict[str, Any]] = []
    page_token: str | None = None
    seen_tokens: set[str] = set()
    while True:
        query: dict[str, Any] = {"pageSize": PAGE_SIZE, **(params or {})}
        if page_token:
            query["pageToken"] = page_token
        response = api_session.get(url, params=query, timeout=TIMEOUT)
        response.raise_for_status()
        body = response.json()
        results.extend(body.get(items_key) or [])
        page_token = body.get("nextPageToken")
        if not page_token:
            return results
        if page_token in seen_tokens:
            raise RuntimeError(
                f"Fireworks AI returned a repeated page token for {url}.",
            )
        seen_tokens.add(page_token)


def resource_id(resource_name: str) -> str:
    """Return the last segment of a resource name, such as `bob` for `accounts/a/users/bob`."""
    return resource_name.rsplit("/", 1)[-1]


def is_access_denied(error: requests.HTTPError) -> bool:
    """Report whether a request failed because the API key cannot read the resource."""
    return error.response is not None and error.response.status_code in (403, 404)


def to_int(value: Any) -> int | None:
    """Convert an int64 that the API returns as a JSON string."""
    if value is None or value == "":
        return None
    return int(value)
