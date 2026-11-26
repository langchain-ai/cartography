import copy
import json

import pytest
import requests

from cartography.intel.workshop import inventory
from tests.data.workshop import API_KEY
from tests.data.workshop import API_URL
from tests.data.workshop import GROUP_MEMBERS
from tests.data.workshop import GROUPS
from tests.data.workshop import HOSTS
from tests.data.workshop import response
from tests.data.workshop import USERS


@pytest.mark.parametrize(
    "method,field,items",
    [
        ("ListHosts", "hosts", HOSTS),
        ("ListUsers", "users", USERS),
        ("ListTags", "tags", [{"tag": "synthetic"}]),
        ("ListGroups", "groups", GROUPS),
        ("ListGroupMembers", "members", USERS),
    ],
)
@pytest.mark.parametrize("terminal_more", [False, None])
def test_numbered_paging_and_transport(mocker, method, field, items, terminal_more):
    # Arrange
    identity = (
        "uuid" if method == "ListHosts" else "tag" if method == "ListTags" else "id"
    )
    kwargs = {"group_id": "synthetic-group"} if method == "ListGroupMembers" else {}
    next_items = [{**items[0], identity: "synthetic-next"}]
    pages = [{field: items, "more": True}, {field: next_items}]
    if terminal_more is False:
        pages[1]["more"] = False
    else:
        pages.append({})
    get = mocker.patch(
        "cartography.intel.workshop.inventory.requests.get",
        side_effect=[response(p) for p in pages],
    )

    # Act
    result = inventory.get(API_URL, API_KEY, method, **kwargs)

    # Assert
    assert result == items + next_items
    assert [json.loads(c.kwargs["params"]["message"]) for c in get.call_args_list] == [
        {
            "pageSize": 100,
            "page": page,
            **({"groupId": "synthetic-group"} if kwargs else {}),
        }
        for page in range(1, len(pages) + 1)
    ]
    for call in get.call_args_list:
        assert call.args == (API_URL + "/workshop.v1.WorkshopService/" + method,)
        assert call.kwargs["headers"] == {"Authorization": API_KEY}
        assert call.kwargs["allow_redirects"] is False
        assert call.kwargs["timeout"] == (10, 60)
        assert call.kwargs["params"]["encoding"] == "json"


def test_explicit_terminal_page_and_protobuf_count(mocker):
    # Arrange
    get = mocker.patch(
        "cartography.intel.workshop.inventory.requests.get",
        return_value=response({"hosts": HOSTS, "more": False, "count": "1"}),
    )

    # Act
    result = inventory.get(API_URL, API_KEY, "ListHosts")

    # Assert
    assert result == HOSTS
    assert get.call_count == 1


def test_legacy_short_page_requires_empty_terminal(mocker):
    # Arrange
    get = mocker.patch(
        "cartography.intel.workshop.inventory.requests.get",
        side_effect=[response({"hosts": HOSTS}), response({})],
    )

    # Act
    result = inventory.get(API_URL, API_KEY, "ListHosts")

    # Assert
    assert result == HOSTS
    assert get.call_count == 2


@pytest.mark.parametrize("payload", [{}, {"hosts": []}, {"more": False, "count": "0"}])
def test_empty_inventory(mocker, payload):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.inventory.requests.get",
        return_value=response(payload),
    )

    # Act and assert
    assert inventory.get(API_URL, API_KEY, "ListHosts") == []


@pytest.mark.parametrize(
    "payload",
    [
        [],
        None,
        {"hosts": None},
        {"hosts": [None]},
        {"hosts": [{}]},
        {"hosts": [{"uuid": " "}]},
        {"hosts": [{"uuid": True}]},
        {"hosts": HOSTS, "more": "false"},
        {"hosts": HOSTS, "more": None},
        {"more": True},
        {"hosts": HOSTS * 2},
        {"nextPageToken": "synthetic"},
        {"hosts": HOSTS, "count": True},
        {"hosts": HOSTS, "count": "-1"},
        {"hosts": HOSTS, "count": 1.0},
        {"hosts": HOSTS, "count": 0},
        {"hosts": HOSTS, "more": False, "count": "2"},
        {"hosts": HOSTS, "more": False, "count": "10001"},
    ],
)
def test_invalid_pages_fail_closed(mocker, payload):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.inventory.requests.get",
        return_value=response(payload),
    )

    # Act and assert
    with pytest.raises(ValueError):
        inventory.get(API_URL, API_KEY, "ListHosts")


@pytest.mark.parametrize(
    "pages",
    [
        [{"hosts": HOSTS}, {"hosts": HOSTS}],
        [{"hosts": HOSTS, "count": "2"}, {"count": "3"}],
        [{"hosts": HOSTS, "count": "2"}, {}],
        [{"hosts": HOSTS, "more": True}, {}],
        [
            {"hosts": HOSTS, "more": True},
            {"hosts": [{"uuid": "synthetic-host-2"}], "more": True},
        ],
    ],
)
def test_repeats_changed_counts_and_bounds(mocker, pages):
    # Arrange
    mocker.patch.object(inventory, "MAX_PAGES", 2)
    mocker.patch(
        "cartography.intel.workshop.inventory.requests.get",
        side_effect=[response(p) for p in pages],
    )

    # Act and assert
    with pytest.raises(ValueError):
        inventory.get(API_URL, API_KEY, "ListHosts")


@pytest.mark.parametrize("status", [204, 302, 401, 403, 429, 500])
def test_http_failure(mocker, status):
    # Arrange
    mocker.patch(
        "cartography.intel.workshop.inventory.requests.get",
        return_value=response({}, status),
    )

    # Act and assert
    with pytest.raises((ValueError, requests.HTTPError)):
        inventory.get(API_URL, API_KEY, "ListHosts")


@pytest.mark.parametrize(
    "url",
    [
        "http://example.invalid",
        "https://user@example.invalid",
        "https://example.invalid/path",
        "https://example.invalid?x=y",
        "https://example.invalid#fragment",
    ],
)
def test_invalid_origins(mocker, url):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.inventory.requests.get")

    # Act and assert
    with pytest.raises(ValueError):
        inventory.get(url, API_KEY, "ListHosts")
    get.assert_not_called()


def test_selected_host_and_directory_fields():
    # Arrange
    raw = copy.deepcopy(HOSTS)
    raw[0]["lastSeenClientMode"] = "MONITOR"
    raw[0]["configuredClientMode"] = "LOCKDOWN"
    raw_users = copy.deepcopy(USERS)
    raw_users[0]["profilePictureUrl"] = "https://example.invalid/private"

    # Act
    users = inventory.transform_users(raw_users, "tenant-a")
    hosts = inventory.transform_hosts(raw, users, "tenant-a")

    # Assert
    assert users == [
        {
            "id": '["tenant-a","synthetic-user-1"]',
            "user_id": "synthetic-user-1",
            "username": "synthetic-user@example.invalid",
            "manager_email": "synthetic-manager@example.invalid",
            "department_name": "Synthetic Department",
            "cost_center_name": "Synthetic Cost Center",
            "directory_type": "DIRECTORY_TYPE_DSYNC",
        }
    ]
    assert hosts[0]["hostname"] == "synthetic-workstation"
    assert hosts[0]["last_sync"] == "2026-01-01T00:00:00Z"
    assert hosts[0]["primary_user_id"] == users[0]["id"]
    assert hosts[0]["primary_user_groups"] == ["synthetic-group"]
    assert hosts[0]["tag_ids"] == [
        '["tenant-a","global"]',
        '["tenant-a","synthetic-team"]',
        '["tenant-a","synthetic-inventory-only"]',
    ]
    assert not any(key.endswith("_mode") for key in hosts[0])
    assert "profilePictureUrl" not in users[0]


@pytest.mark.parametrize(
    "users", [[], USERS + [{"id": "synthetic-other", "username": USERS[0]["username"]}]]
)
def test_primary_user_is_not_guessed(users):
    # Arrange
    transformed = inventory.transform_users(users, "tenant-a")

    # Act
    host = inventory.transform_hosts(HOSTS, transformed, "tenant-a")[0]

    # Assert
    assert host["primary_user"] == USERS[0]["username"]
    assert host["primary_user_id"] is None


@pytest.mark.parametrize(
    "patch",
    [
        {"tagsTruncated": True},
        {"tagsTruncated": "false"},
        {"tags": "synthetic"},
        {"tags": [None]},
        {"hostname": 7},
        {"primary_user": "ambiguous"},
        {"primaryUserGroups": "synthetic"},
    ],
)
def test_invalid_host_fields(patch):
    # Arrange
    host = {**HOSTS[0], **patch}

    # Act and assert
    with pytest.raises(ValueError):
        inventory.transform_hosts([host], [], "tenant-a")


@pytest.mark.parametrize(
    "patch",
    [
        {"username": ""},
        {"manager_email": "ambiguous"},
        {"managerEmail": 7},
        {"type": True},
        {"type": 3},
        {"type": "FUTURE"},
    ],
)
def test_invalid_directory_fields(patch):
    # Arrange
    user = {**USERS[0], **patch}

    # Act and assert
    with pytest.raises(ValueError):
        inventory.transform_users([user], "tenant-a")


def test_snake_case_and_omitted_optional_fields():
    # Arrange
    host = {
        "uuid": "synthetic",
        "primary_user": "synthetic-user@example.invalid",
        "primary_user_groups": ["synthetic"],
        "os_version": "99",
        "tags_truncated": False,
    }
    users = inventory.transform_users([{**USERS[0], "type": 2}], "tenant-a")

    # Act
    result = inventory.transform_hosts([host], users, "tenant-a")[0]

    # Assert
    assert result["os_version"] == "99"
    assert result["hostname"] == ""
    assert result["tag_ids"] == ['["tenant-a","global"]']
    assert users[0]["directory_type"] == "DIRECTORY_TYPE_LOCAL"


@pytest.mark.parametrize("group_id", [None, "", " ", 1])
def test_members_require_explicit_group(mocker, group_id):
    # Arrange
    get = mocker.patch("cartography.intel.workshop.inventory.requests.get")

    # Act and assert
    with pytest.raises(ValueError):
        inventory.get(API_URL, API_KEY, "ListGroupMembers", group_id)
    get.assert_not_called()


def test_selected_group_fields_and_complete_memberships():
    # Arrange
    users = inventory.transform_users(USERS, "tenant-a")

    # Act
    groups = inventory.transform_groups(GROUPS, GROUP_MEMBERS, users, "tenant-a")

    # Assert
    assert len(groups) == 12
    assert groups[0] == {
        "id": '["tenant-a","synthetic-group-0"]',
        "group_id": "synthetic-group-0",
        "name": "Synthetic Group 0",
        "description": "Synthetic directory group",
        "directory_type": "DIRECTORY_TYPE_DSYNC",
        "idp_id": "synthetic-idp-group-0",
        "tags_managed": True,
        "tag_ids": [
            '["tenant-a","synthetic-team"]',
            '["tenant-a","synthetic-group-only"]',
        ],
        "member_ids": ['["tenant-a","synthetic-user-1"]'],
    }


@pytest.mark.parametrize(
    "patch",
    [
        {"name": ""},
        {"description": 7},
        {"type": True},
        {"type": "FUTURE"},
        {"tagsManaged": "false"},
        {"tags_managed": False},
        {"idp_id": "ambiguous"},
        {"tags": [None]},
    ],
)
def test_invalid_group_fields(patch):
    # Arrange
    users = inventory.transform_users(USERS, "tenant-a")

    # Act and assert
    with pytest.raises(ValueError):
        inventory.transform_groups(
            [{**GROUPS[0], **patch}], GROUP_MEMBERS, users, "tenant-a"
        )


def test_unknown_directory_member_fails_closed():
    # Arrange
    members = {GROUPS[0]["id"]: [{"id": "synthetic-missing-user"}]}
    users = inventory.transform_users(USERS, "tenant-a")

    # Act and assert
    with pytest.raises(ValueError, match="missing from ListUsers"):
        inventory.transform_groups(GROUPS[:1], members, users, "tenant-a")


def test_group_snake_case_and_empty_members():
    # Arrange
    group = {
        "id": "synthetic-group",
        "name": "Synthetic",
        "idp_id": "synthetic-idp",
        "tags_managed": False,
        "type": 2,
    }

    # Act
    result = inventory.transform_groups([group], {group["id"]: []}, [], "tenant-a")[0]

    # Assert
    assert result["directory_type"] == "DIRECTORY_TYPE_LOCAL"
    assert result["idp_id"] == "synthetic-idp"
    assert result["tags_managed"] is False
    assert result["member_ids"] == result["tag_ids"] == []


@pytest.mark.parametrize("tags", [[], ["global"], ["global", "global"]])
def test_global_membership_is_always_present_once(tags):
    # Arrange
    host = {"uuid": "synthetic-host", "tags": tags}

    # Act
    result = inventory.transform_hosts([host], [], "tenant-a")[0]

    # Assert
    assert result["tag_ids"] == ['["tenant-a","global"]']
