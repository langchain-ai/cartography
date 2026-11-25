from typing import Any
from unittest.mock import MagicMock

import requests

import cartography.intel.baseten.apikeys
import cartography.intel.baseten.environment_groups
import cartography.intel.baseten.models
import cartography.intel.baseten.organization
import cartography.intel.baseten.secrets
from cartography.config import Config
from cartography.intel.baseten import start_baseten_ingestion
from cartography.intel.baseten.util import paginated_get
from tests.data.baseten.apikeys import BASETEN_API_KEYS
from tests.data.baseten.environment_groups import BASETEN_ENVIRONMENT_GROUPS_BY_TEAM
from tests.data.baseten.models import BASETEN_DEPLOYMENTS
from tests.data.baseten.organization import BASETEN_ORGANIZATION

BASE_URL = "https://api.baseten.co"


def _session(bodies: dict[tuple[str, str | None], dict[str, Any]]) -> MagicMock:
    """Build a fake requests session that answers GETs by (URL, cursor)."""

    def get(url: str, params: dict[str, Any] | None = None, timeout=None):
        response = MagicMock(spec=requests.Response)
        response.json.return_value = bodies[(url, (params or {}).get("cursor"))]
        response.raise_for_status.return_value = None
        return response

    session = MagicMock(spec=requests.Session)
    session.get.side_effect = get
    return session


def test_paginated_get_follows_cursor():
    # Arrange
    url = f"{BASE_URL}/v1/users"
    session = _session(
        {
            (url, None): {
                "items": [{"user_id": "u1"}],
                "pagination": {"has_more": True, "cursor": "c1"},
            },
            (url, "c1"): {
                "items": [{"user_id": "u2"}],
                "pagination": {"has_more": False, "cursor": None},
            },
        },
    )

    # Act
    result = paginated_get(session, url)

    # Assert
    assert result == [{"user_id": "u1"}, {"user_id": "u2"}]


def test_environment_groups_get_reads_each_team():
    # Arrange
    session = _session(
        {
            (f"{BASE_URL}/v1/teams/{team_id}/environment_groups", None): body
            for team_id, body in BASETEN_ENVIRONMENT_GROUPS_BY_TEAM.items()
        },
    )

    # Act
    groups = cartography.intel.baseten.environment_groups.get(
        session,
        BASE_URL,
        ["team_default01", "team_research01"],
    )

    # Assert
    assert [group["name"] for group in groups] == ["production", "staging"]


def test_secrets_get_and_transform_attach_team_id():
    # Arrange
    session = _session(
        {
            (f"{BASE_URL}/v1/teams/team_a/secrets", None): {
                "secrets": [{"id": "s1", "name": "one", "team_name": "A"}],
            },
            (f"{BASE_URL}/v1/teams/team_b/secrets", None): {"secrets": []},
        },
    )

    # Act
    secrets = cartography.intel.baseten.secrets.transform(
        cartography.intel.baseten.secrets.get(
            session,
            BASE_URL,
            [{"id": "team_a"}, {"id": "team_b"}],
        ),
    )

    # Assert
    assert secrets == [
        {"id": "s1", "name": "one", "team_name": "A", "team_id": "team_a"},
    ]


def test_get_deployments_reads_each_model():
    # Arrange
    session = _session(
        {
            (f"{BASE_URL}/v1/models/{model_id}/deployments", None): body
            for model_id, body in BASETEN_DEPLOYMENTS.items()
        },
    )

    # Act
    deployments = cartography.intel.baseten.models.get_deployments(
        session,
        BASE_URL,
        list(BASETEN_DEPLOYMENTS),
    )

    # Assert
    assert {deployment["id"] for deployment in deployments} == {
        "dep_llama_v2",
        "dep_llama_v1",
        "dep_whisper_v1",
    }


def test_transform_organization_omits_external_id():
    # Act
    organization = cartography.intel.baseten.organization.transform(
        BASETEN_ORGANIZATION,
    )

    # Assert
    assert organization["aws_assume_role_enabled"] is True
    assert "ext-springfield" not in organization.values()


def test_transform_organization_without_aws_assume_role():
    # Act
    organization = cartography.intel.baseten.organization.transform(
        {**BASETEN_ORGANIZATION, "aws_assume_role": None},
    )

    # Assert
    assert organization["aws_assume_role_enabled"] is False
    assert organization["aws_assume_role_baseten_role_arn"] is None


def test_transform_apikeys_resolves_team_and_owner():
    # Act
    apikeys = cartography.intel.baseten.apikeys.transform(
        BASETEN_API_KEYS["keys"],
        {"Default": "team_default01"},
    )

    # Assert
    by_prefix = {apikey["prefix"]: apikey for apikey in apikeys}
    assert by_prefix["abCD1234"]["owner_user_id"] == "user_homer01"
    assert by_prefix["abCD1234"]["team_id"] is None
    assert by_prefix["efGH5678"]["team_id"] == "team_default01"
    # A team the API key can't see stays unlinked rather than guessed.
    assert by_prefix["ijKL9012"]["team_id"] is None


def test_transform_deployments_flattens_settings():
    # Act
    deployments = cartography.intel.baseten.models.transform_deployments(
        BASETEN_DEPLOYMENTS["model_llama01"]["deployments"],
    )

    # Assert
    assert deployments[0]["min_replica"] == 1
    assert deployments[0]["region"] == "us-west"
    assert deployments[1]["min_replica"] is None
    assert deployments[1]["region"] is None


def test_start_baseten_ingestion_skips_without_api_key():
    # Arrange
    neo4j_session = MagicMock()
    config = Config(neo4j_uri="bolt://localhost:7687", update_tag=1)

    # Act
    start_baseten_ingestion(neo4j_session, config)

    # Assert
    neo4j_session.run.assert_not_called()
