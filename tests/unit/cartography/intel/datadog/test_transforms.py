from cartography.intel.datadog import organization
from cartography.intel.datadog import roles
from cartography.intel.datadog import users
from tests.data.datadog import api as fixtures


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
    assert service_accounts[1]["role_ids"] == [fixtures.AUDITOR_ROLE_ID]


def test_users_transform_keeps_identity_fields_only():
    # Act
    people, service_accounts = users.transform(fixtures.NAMED_USERS)

    # Assert
    assert {key for person in people for key in person} == {
        "id",
        "status",
        "disabled",
        "created_at",
        "modified_at",
        "role_ids",
    }
    assert {key for sa in service_accounts for key in sa} == {
        "id",
        "name",
        "email",
        "status",
        "disabled",
        "created_at",
        "modified_at",
        "role_ids",
    }
    values = {str(value) for person in people for value in person.values()}
    assert not values & set(fixtures.PROFILE_SENTINELS)
    assert not values & set(fixtures.HUMAN_EMAILS)
    assert not any("@" in value for value in values)


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
