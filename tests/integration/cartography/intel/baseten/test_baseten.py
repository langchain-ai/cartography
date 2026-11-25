from unittest.mock import patch

import cartography.intel.baseten
import cartography.intel.baseten.apikeys
import cartography.intel.baseten.chains
import cartography.intel.baseten.environment_groups
import cartography.intel.baseten.models
import cartography.intel.baseten.organization
import cartography.intel.baseten.secrets
import cartography.intel.baseten.teams
import cartography.intel.baseten.users
import tests.data.baseten.apikeys
import tests.data.baseten.chains
import tests.data.baseten.environment_groups
import tests.data.baseten.models
import tests.data.baseten.organization
import tests.data.baseten.secrets
import tests.data.baseten.teams
import tests.data.baseten.users
from cartography.config import Config
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org_springfield01"

TEAMS = tests.data.baseten.teams.BASETEN_TEAMS["teams"]
MODELS = tests.data.baseten.models.BASETEN_MODELS["models"]
DEPLOYMENTS = [
    deployment
    for body in tests.data.baseten.models.BASETEN_DEPLOYMENTS.values()
    for deployment in body["deployments"]
]
CHAINS = tests.data.baseten.chains.BASETEN_CHAINS["chains"]
API_KEYS = tests.data.baseten.apikeys.BASETEN_API_KEYS["keys"]
ENVIRONMENT_GROUPS = [
    group
    for body in tests.data.baseten.environment_groups.BASETEN_ENVIRONMENT_GROUPS_BY_TEAM.values()
    for group in body["items"]
]


def _run_sync(neo4j_session, update_tag: int, api_keys: list[dict]) -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        baseten_api_key="test-key",
    )
    with (
        patch.object(
            cartography.intel.baseten.organization,
            "get",
            return_value=tests.data.baseten.organization.BASETEN_ORGANIZATION,
        ),
        patch.object(cartography.intel.baseten.teams, "get", return_value=TEAMS),
        patch.object(
            cartography.intel.baseten.users,
            "get",
            return_value=tests.data.baseten.users.BASETEN_USERS,
        ),
        patch.object(cartography.intel.baseten.models, "get", return_value=MODELS),
        patch.object(
            cartography.intel.baseten.models,
            "get_deployments",
            return_value=DEPLOYMENTS,
        ),
        patch.object(cartography.intel.baseten.chains, "get", return_value=CHAINS),
        patch.object(
            cartography.intel.baseten.secrets,
            "get",
            return_value=tests.data.baseten.secrets.BASETEN_SECRETS_BY_TEAM,
        ),
        patch.object(cartography.intel.baseten.apikeys, "get", return_value=api_keys),
        patch.object(
            cartography.intel.baseten.environment_groups,
            "get",
            return_value=ENVIRONMENT_GROUPS,
        ),
    ):
        cartography.intel.baseten.start_baseten_ingestion(neo4j_session, config)


def test_sync_baseten(neo4j_session):
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'Baseten') DETACH DELETE n"
    )

    # Act
    _run_sync(neo4j_session, TEST_UPDATE_TAG, API_KEYS)

    # Assert
    assert check_nodes(
        neo4j_session,
        "BasetenOrganization",
        [
            "id",
            "name",
            "allow_personal_api_keys",
            "aws_assume_role_enabled",
            "aws_assume_role_baseten_role_arn",
        ],
    ) == {
        (
            TEST_ORG_ID,
            "Springfield Nuclear",
            True,
            True,
            "arn:aws:iam::111122223333:role/baseten-assume-role",
        ),
    }
    assert check_nodes(neo4j_session, "BasetenTeam", ["id", "name", "default"]) == {
        ("team_default01", "Default", True),
        ("team_research01", "Research", False),
    }
    assert check_nodes(neo4j_session, "BasetenUser", ["id", "email"]) == {
        ("user_homer01", "hjsimpson@simpson.corp"),
        ("user_marge01", "mbsimpson@simpson.corp"),
    }
    assert check_nodes(
        neo4j_session,
        "BasetenDeployment",
        ["id", "status", "is_production", "min_replica", "max_replica", "region"],
    ) == {
        ("dep_llama_v2", "ACTIVE", True, 1, 4, "us-west"),
        ("dep_llama_v1", "SCALED_TO_ZERO", False, None, None, None),
        ("dep_whisper_v1", "BUILD_FAILED", False, None, None, None),
    }
    assert check_nodes(neo4j_session, "BasetenSecret", ["id", "name"]) == {
        ("secret_hf01", "hf_access_token"),
        ("secret_wandb01", "wandb_api_key"),
    }
    assert check_nodes(
        neo4j_session,
        "BasetenApiKey",
        ["id", "type", "owner_email"],
    ) == {
        ("abCD1234", "PERSONAL", "hjsimpson@simpson.corp"),
        ("efGH5678", "WORKSPACE_INVOKE", None),
        ("ijKL9012", "WORKSPACE_MANAGE_ALL", None),
    }
    assert check_nodes(
        neo4j_session,
        "BasetenEnvironmentGroup",
        ["id", "is_restricted"],
    ) == {
        ("team_default01/production", True),
        ("team_default01/staging", False),
    }

    # Every node is scoped to the organization.
    for label, ids in (
        ("BasetenTeam", {"team_default01", "team_research01"}),
        ("BasetenUser", {"user_homer01", "user_marge01"}),
        ("BasetenModel", {"model_llama01", "model_whisper01"}),
        ("BasetenDeployment", {"dep_llama_v2", "dep_llama_v1", "dep_whisper_v1"}),
        ("BasetenChain", {"chain_rag01"}),
        ("BasetenSecret", {"secret_hf01", "secret_wandb01"}),
        ("BasetenApiKey", {"abCD1234", "efGH5678", "ijKL9012"}),
        (
            "BasetenEnvironmentGroup",
            {"team_default01/production", "team_default01/staging"},
        ),
    ):
        assert check_rels(
            neo4j_session,
            "BasetenOrganization",
            "id",
            label,
            "id",
            "RESOURCE",
            rel_direction_right=True,
        ) == {(TEST_ORG_ID, node_id) for node_id in ids}

    # Team-owned resources are linked to their team by the team name Baseten reports.
    assert check_rels(
        neo4j_session,
        "BasetenTeam",
        "id",
        "BasetenModel",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("team_default01", "model_llama01"),
        ("team_research01", "model_whisper01"),
    }
    assert check_rels(
        neo4j_session,
        "BasetenTeam",
        "id",
        "BasetenChain",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("team_research01", "chain_rag01")}
    assert check_rels(
        neo4j_session,
        "BasetenTeam",
        "id",
        "BasetenSecret",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("team_default01", "secret_hf01"),
        ("team_research01", "secret_wandb01"),
    }
    assert check_rels(
        neo4j_session,
        "BasetenTeam",
        "id",
        "BasetenApiKey",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("team_default01", "efGH5678"),
        ("team_research01", "ijKL9012"),
    }
    assert check_rels(
        neo4j_session,
        "BasetenTeam",
        "id",
        "BasetenEnvironmentGroup",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("team_default01", "team_default01/production"),
        ("team_default01", "team_default01/staging"),
    }

    assert check_rels(
        neo4j_session,
        "BasetenModel",
        "id",
        "BasetenDeployment",
        "id",
        "HAS_DEPLOYMENT",
        rel_direction_right=True,
    ) == {
        ("model_llama01", "dep_llama_v2"),
        ("model_llama01", "dep_llama_v1"),
        ("model_whisper01", "dep_whisper_v1"),
    }
    assert check_rels(
        neo4j_session,
        "BasetenApiKey",
        "id",
        "BasetenUser",
        "id",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {("abCD1234", "user_homer01")}
    assert check_rels(
        neo4j_session,
        "BasetenApiKey",
        "id",
        "BasetenModel",
        "id",
        "SCOPED_TO",
        rel_direction_right=True,
    ) == {("efGH5678", "model_llama01")}
    assert check_rels(
        neo4j_session,
        "BasetenUser",
        "id",
        "BasetenEnvironmentGroup",
        "id",
        "CAN_MANAGE",
        rel_direction_right=True,
    ) == {("user_marge01", "team_default01/production")}

    # Ontology semantic labels are applied.
    assert check_nodes(neo4j_session, "UserAccount", ["id", "_ont_email"]) >= {
        ("user_homer01", "hjsimpson@simpson.corp"),
        ("user_marge01", "mbsimpson@simpson.corp"),
    }
    assert check_nodes(neo4j_session, "BasetenApiKey", ["id", "_ont_name"]) == {
        ("abCD1234", "homer-laptop"),
        ("efGH5678", "production-inference"),
        ("ijKL9012", "ijKL9012"),
    }


def test_sync_baseten_cleans_up_revoked_api_keys(neo4j_session):
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE any(l IN labels(n) WHERE l STARTS WITH 'Baseten') DETACH DELETE n"
    )
    _run_sync(neo4j_session, TEST_UPDATE_TAG, API_KEYS)

    # Act
    _run_sync(neo4j_session, TEST_UPDATE_TAG + 1, API_KEYS[1:])

    # Assert
    assert check_nodes(neo4j_session, "BasetenApiKey", ["id", "lastupdated"]) == {
        ("efGH5678", TEST_UPDATE_TAG + 1),
        ("ijKL9012", TEST_UPDATE_TAG + 1),
    }
    assert (
        check_rels(
            neo4j_session,
            "BasetenApiKey",
            "id",
            "BasetenUser",
            "id",
            "OWNED_BY",
            rel_direction_right=True,
        )
        == set()
    )
