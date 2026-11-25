from unittest.mock import patch

import cartography.intel.anthropic
import cartography.intel.anthropic.apikeys
import cartography.intel.anthropic.compliance
import cartography.intel.anthropic.users
import cartography.intel.anthropic.workspaces
import tests.data.anthropic.compliance
import tests.data.anthropic.users
from cartography.config import Config
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


@patch.object(
    cartography.intel.anthropic.compliance,
    "get_settings",
    return_value=tests.data.anthropic.compliance.ANTHROPIC_COMPLIANCE_SETTINGS,
)
@patch.object(
    cartography.intel.anthropic.compliance,
    "get_organizations",
    return_value=tests.data.anthropic.compliance.ANTHROPIC_COMPLIANCE_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.anthropic.apikeys, "get", return_value=(TEST_ORG_ID, [])
)
@patch.object(
    cartography.intel.anthropic.workspaces, "get", return_value=(TEST_ORG_ID, [])
)
@patch.object(
    cartography.intel.anthropic.users,
    "get",
    return_value=(TEST_ORG_ID, tests.data.anthropic.users.ANTHROPIC_USERS),
)
def test_compliance_settings_are_set_on_the_admin_api_organization(
    mock_users,
    mock_workspaces,
    mock_apikeys,
    mock_organizations,
    mock_settings,
    neo4j_session,
):
    """
    Ensure the Compliance API settings land on the organization that the Admin
    API sync creates, and the users sync doesn't clear them.
    """
    # Arrange
    neo4j_session.run("MATCH (n:AnthropicOrganization) DETACH DELETE n")
    config = Config(
        neo4j_uri="bolt://unused",
        update_tag=TEST_UPDATE_TAG,
        anthropic_apikey="sk-ant-admin01-test",
        anthropic_compliance_apikey="sk-ant-api01-test",
    )

    # Act
    cartography.intel.anthropic.start_anthropic_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(
        neo4j_session,
        "AnthropicOrganization",
        [
            "id",
            "api_zero_data_retention_enabled",
            "claude_code_zero_data_retention_enabled",
        ],
    ) == {(TEST_ORG_ID, True, None)}


@patch.object(
    cartography.intel.anthropic.compliance,
    "get_settings",
    return_value=tests.data.anthropic.compliance.ANTHROPIC_COMPLIANCE_SETTINGS,
)
@patch.object(
    cartography.intel.anthropic.compliance,
    "get_organizations",
    return_value=tests.data.anthropic.compliance.ANTHROPIC_COMPLIANCE_ORGANIZATIONS,
)
@patch.object(cartography.intel.anthropic.users, "get")
def test_compliance_key_alone_syncs_organization_settings(
    mock_users,
    mock_organizations,
    mock_settings,
    neo4j_session,
):
    """
    Ensure a Compliance Access Key works without an Admin API key and doesn't
    call the Admin API.
    """
    # Arrange
    neo4j_session.run("MATCH (n:AnthropicOrganization) DETACH DELETE n")
    config = Config(
        neo4j_uri="bolt://unused",
        update_tag=TEST_UPDATE_TAG,
        anthropic_compliance_apikey="sk-ant-api01-test",
    )

    # Act
    cartography.intel.anthropic.start_anthropic_ingestion(neo4j_session, config)

    # Assert
    mock_users.assert_not_called()
    assert check_nodes(
        neo4j_session,
        "AnthropicOrganization",
        ["id", "api_zero_data_retention_enabled"],
    ) == {(TEST_ORG_ID, True)}
