from unittest.mock import MagicMock

import pytest

from cartography.intel.fireworks.util import PAGE_SIZE
from cartography.intel.fireworks.util import paginated_get


def _response(body: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = body
    return response


def test_paginated_get_follows_next_page_token():
    # Arrange
    api_session = MagicMock()
    api_session.get.side_effect = [
        _response({"users": [{"name": "a"}], "nextPageToken": "t1"}),
        _response({"users": [], "nextPageToken": "t2"}),
        _response({"users": [{"name": "b"}]}),
    ]

    # Act
    results = paginated_get(api_session, "https://example/users", "users")

    # Assert
    assert results == [{"name": "a"}, {"name": "b"}]
    page_tokens = [
        call.kwargs["params"].get("pageToken")
        for call in api_session.get.call_args_list
    ]
    assert page_tokens == [None, "t1", "t2"]
    assert all(
        call.kwargs["params"]["pageSize"] == PAGE_SIZE
        for call in api_session.get.call_args_list
    )


def test_paginated_get_stops_on_a_repeated_page_token():
    # Arrange
    api_session = MagicMock()
    api_session.get.return_value = _response(
        {"users": [{"name": "a"}], "nextPageToken": "same"},
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="repeated page token"):
        paginated_get(api_session, "https://example/users", "users")
