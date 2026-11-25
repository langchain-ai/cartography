from typing import Any

import requests

BASE_URL = "https://api.baseten.co"

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
TIMEOUT = (60, 60)


def get_json(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a GET request to the Baseten Management API and return the JSON body."""
    response = api_session.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def paginated_get(
    api_session: requests.Session,
    url: str,
) -> list[dict[str, Any]]:
    """Read every page of a cursor-paginated Baseten Management API list.

    Paginated endpoints return `items` and a `pagination` object whose `cursor` is
    passed back to fetch the next page while `has_more` is true.
    """
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {}
    while True:
        body = get_json(api_session, url, params=params)
        results.extend(body["items"])
        pagination = body.get("pagination") or {}
        cursor = pagination.get("cursor")
        if not pagination.get("has_more") or not cursor:
            return results
        params = {"cursor": cursor}


def team_id_for_name(
    team_ids_by_name: dict[str, str],
    team_name: str | None,
) -> str | None:
    """Resolve a team name, which is unique in an organization, to the team's ID."""
    if not team_name:
        return None
    return team_ids_by_name.get(team_name)
