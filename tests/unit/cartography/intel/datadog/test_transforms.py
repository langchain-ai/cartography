from cartography.intel.datadog import accesstokens
from cartography.intel.datadog import apikeys
from cartography.intel.datadog import applicationkeys
from cartography.intel.datadog import organization
from cartography.intel.datadog import roles
from cartography.intel.datadog import users
from tests.data.datadog import api as fixtures


def _values(records: list[dict]) -> set[str]:
    return {str(value) for record in records for value in record.values()}


def test_users_transform_splits_service_accounts():
    # Act
    people, service_accounts = users.transform(fixtures.NAMED_USERS)

    # Assert
    assert [user["id"] for user in people] == [
        fixtures.ALICE_ID,
        fixtures.BOB_ID,
        fixtures.CAROL_ID,
    ]
    assert [sa["id"] for sa in service_accounts] == [
        fixtures.CI_SA_ID,
        fixtures.CARTOGRAPHY_SA_ID,
    ]
    assert people[0]["role_ids"] == sorted(
        [fixtures.ADMIN_ROLE_ID, fixtures.READ_ONLY_ROLE_ID],
    )
    assert people[0]["mfa_enabled"] is True
    assert people[2]["mfa_enabled"] is None
    assert "mfa_enabled" not in service_accounts[0]


def test_roles_transform_resolves_permission_names():
    # Act
    result = {
        role["id"]: role
        for role in roles.transform(fixtures.ROLES, fixtures.PERMISSIONS)
    }

    # Assert
    assert result[fixtures.STANDARD_ROLE_ID]["permissions"] == [
        "dashboards_read",
        "user_access_read",
    ]
    # A permission missing from /api/v2/permissions keeps its ID.
    assert "perm-9999" in result[fixtures.AUDITOR_ROLE_ID]["permissions"]


def test_organization_transform_reads_included_org():
    # Act
    result = organization.transform(fixtures.CURRENT_USER, "https://api.datadoghq.com")

    # Assert
    assert result == {
        "id": fixtures.ORG_ID,
        "name": "Example Corp",
        "public_id": "abc123def",
        "api_base_url": "https://api.datadoghq.com",
    }


def test_key_transforms_drop_secret_values():
    # Act
    records = (
        apikeys.transform(fixtures.API_KEYS)
        + applicationkeys.transform(fixtures.APPLICATION_KEYS)
        + accesstokens.transform(fixtures.ACCESS_TOKENS)
    )

    # Assert
    assert all("key" not in record for record in records)
    assert all("public_portion" not in record for record in records)
    assert not _values(records) & set(fixtures.FAKE_SECRETS)


def test_application_key_scoping():
    # Act
    result = {
        key["id"]: key for key in applicationkeys.transform(fixtures.APPLICATION_KEYS)
    }

    # Assert
    assert result["appkey-0001"]["scopes"] is None
    assert result["appkey-0001"]["is_scoped"] is False
    assert result["appkey-0002"]["is_scoped"] is True
    assert result["appkey-0002"]["scopes"] == [
        "api_keys_read",
        "org_app_keys_read",
        "user_access_read",
    ]
    assert result["appkey-0003"]["is_scoped"] is False


def test_access_token_types_and_owners():
    # Act
    result = {
        token["id"]: token for token in accesstokens.transform(fixtures.ACCESS_TOKENS)
    }

    # Assert
    assert result["pat-0001"]["token_type"] == "personal"
    assert result["pat-0001"]["owner_id"] == fixtures.ALICE_ID
    assert result["sat-0001"]["token_type"] == "service"
    assert result["sat-0001"]["owner_id"] == fixtures.CI_SA_ID
    assert result["sat-0001"]["leaked"] is None
