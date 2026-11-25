from contextlib import contextmanager
from typing import Any
from typing import Iterator
from unittest.mock import patch

import requests

import cartography.intel.fireworks
import cartography.intel.fireworks.account
import cartography.intel.fireworks.apikeys
import cartography.intel.fireworks.datasets
import cartography.intel.fireworks.deployments
import cartography.intel.fireworks.identityproviders
import cartography.intel.fireworks.models
import cartography.intel.fireworks.secrets
import cartography.intel.fireworks.users
import tests.data.fireworks.account
import tests.data.fireworks.apikeys
import tests.data.fireworks.datasets
import tests.data.fireworks.deployments
import tests.data.fireworks.identityproviders
import tests.data.fireworks.models
import tests.data.fireworks.secrets
import tests.data.fireworks.users
from cartography.config import Config
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 123456790
ACCOUNT_ID = tests.data.fireworks.account.FIREWORKS_ACCOUNT_ID
PREFIX = f"accounts/{ACCOUNT_ID}"


def _config(update_tag: int) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        fireworks_apikey="fw_test_key",
        fireworks_account_id=ACCOUNT_ID,
    )


def _http_error(status_code: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(response=response)


@contextmanager
def _fireworks_api(**overrides: Any) -> Iterator[None]:
    """Patch every Fireworks AI API read, the module's only external boundary."""
    responses: dict[tuple[Any, str], Any] = {
        (cartography.intel.fireworks.account, "get"): {
            "return_value": tests.data.fireworks.account.FIREWORKS_ACCOUNT,
        },
        (cartography.intel.fireworks.account, "get_policy_settings"): {
            "return_value": (
                tests.data.fireworks.account.FIREWORKS_POLICY_SETTINGS,
                True,
            ),
        },
        (cartography.intel.fireworks.users, "get"): {
            "return_value": tests.data.fireworks.users.FIREWORKS_USERS,
        },
        (cartography.intel.fireworks.apikeys, "get"): {
            "return_value": tests.data.fireworks.apikeys.FIREWORKS_API_KEYS,
        },
        (cartography.intel.fireworks.secrets, "get"): {
            "return_value": tests.data.fireworks.secrets.FIREWORKS_SECRETS,
        },
        (cartography.intel.fireworks.identityproviders, "get"): {
            "return_value": tests.data.fireworks.identityproviders.FIREWORKS_IDENTITY_PROVIDERS,
        },
        (cartography.intel.fireworks.models, "get"): {
            "return_value": tests.data.fireworks.models.FIREWORKS_MODELS,
        },
        (cartography.intel.fireworks.deployments, "get"): {
            "return_value": tests.data.fireworks.deployments.FIREWORKS_DEPLOYMENTS,
        },
        (cartography.intel.fireworks.datasets, "get"): {
            "return_value": tests.data.fireworks.datasets.FIREWORKS_DATASETS,
        },
    }
    for key, value in overrides.items():
        module_name, attr = key.split("__")
        module = getattr(cartography.intel.fireworks, module_name)
        responses[(module, attr)] = value
    patchers = [
        patch.object(module, attr, **kwargs)
        for (module, attr), kwargs in responses.items()
    ]
    for patcher in patchers:
        patcher.start()
    try:
        yield
    finally:
        for patcher in patchers:
            patcher.stop()


def _reset(neo4j_session) -> None:
    neo4j_session.run(
        "MATCH (n) WHERE any(label IN labels(n) WHERE label STARTS WITH 'Fireworks') "
        "DETACH DELETE n",
    )


def test_sync_fireworks_ingests_account_resources(neo4j_session):
    # Arrange
    _reset(neo4j_session)

    # Act
    with _fireworks_api():
        cartography.intel.fireworks.start_fireworks_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG),
        )

    # Assert the account carries its policy settings
    assert check_nodes(
        neo4j_session,
        "FireworksAccount",
        [
            "id",
            "display_name",
            "account_type",
            "suspend_state",
            "residency",
            "cmek_required",
            "zdr_default_enforced",
            "zdr_inference_enforced",
            "zdr_training_enforced",
            "zdr_training_enforcement",
            "default_allow_serverless",
            "model_access_rule_count",
        ],
    ) == {
        (
            ACCOUNT_ID,
            "Springfield Nuclear Power Plant",
            "ENTERPRISE",
            "UNSUSPENDED",
            "US",
            True,
            True,
            True,
            False,
            "NOT_ENFORCED",
            False,
            1,
        ),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id"]) >= {(ACCOUNT_ID,)}

    # Assert humans and service accounts are split
    assert check_nodes(
        neo4j_session, "FireworksUser", ["user_id", "email", "role"]
    ) == {
        ("mburns", "mburns@springfield-nuclear.example", "admin"),
        ("hsimpson", "hsimpson@springfield-nuclear.example", "inference-user"),
    }
    assert check_nodes(
        neo4j_session,
        "FireworksServiceAccount",
        ["user_id", "role", "permission_preset"],
    ) == {("ci-bot", "custom", "deployer")}
    assert check_rels(
        neo4j_session,
        "FireworksAccount",
        "id",
        "FireworksUser",
        "user_id",
        "RESOURCE",
    ) == {(ACCOUNT_ID, "mburns"), (ACCOUNT_ID, "hsimpson")}
    assert check_rels(
        neo4j_session,
        "FireworksAccount",
        "id",
        "FireworksServiceAccount",
        "user_id",
        "RESOURCE",
    ) == {(ACCOUNT_ID, "ci-bot")}

    # Assert API keys are linked to their owners by email
    assert check_nodes(
        neo4j_session,
        "FireworksApiKey",
        ["id", "name", "last_used_at", "is_firepass"],
    ) == {
        ("key_burns_admin", "burns-admin", "2025-12-20T14:15:00Z", False),
        ("key_homer_default", "default", None, True),
        ("key_ci_bot", "github-actions", "2026-01-30T22:00:00Z", False),
    }
    assert check_rels(
        neo4j_session,
        "FireworksApiKey",
        "id",
        "FireworksUser",
        "user_id",
        "OWNED_BY",
    ) == {("key_burns_admin", "mburns"), ("key_homer_default", "hsimpson")}
    assert check_rels(
        neo4j_session,
        "FireworksApiKey",
        "id",
        "FireworksServiceAccount",
        "user_id",
        "OWNED_BY",
    ) == {("key_ci_bot", "ci-bot")}
    assert check_rels(
        neo4j_session,
        "FireworksAccount",
        "id",
        "FireworksApiKey",
        "id",
        "RESOURCE",
    ) == {
        (ACCOUNT_ID, "key_burns_admin"),
        (ACCOUNT_ID, "key_homer_default"),
        (ACCOUNT_ID, "key_ci_bot"),
    }

    # Assert secrets carry names only
    assert check_nodes(neo4j_session, "FireworksSecret", ["id", "key_name"]) == {
        (f"{PREFIX}/secrets/wolfram-alpha", "WOLFRAM_ALPHA_API_KEY"),
        (f"{PREFIX}/secrets/hf-token", "HF_TOKEN"),
    }
    secret_keys = neo4j_session.run(
        "MATCH (s:FireworksSecret) RETURN collect(keys(s)) AS keys",
    ).single()["keys"]
    assert all("value" not in keys for keys in secret_keys)

    # Assert identity providers never store the client secret or metadata XML
    assert check_nodes(
        neo4j_session,
        "FireworksIdentityProvider",
        ["display_name", "protocol", "issuer", "enforce_sso", "jit_default_role"],
    ) == {
        (
            "Okta",
            "SAML",
            "https://springfield.okta.example/app/metadata",
            True,
            None,
        ),
        (
            "Google Workspace",
            "OIDC",
            "https://accounts.google.com",
            False,
            "inference-user",
        ),
    }
    provider_keys = neo4j_session.run(
        "MATCH (p:FireworksIdentityProvider) "
        "UNWIND keys(p) AS key RETURN collect(DISTINCT key) AS keys",
    ).single()["keys"]
    assert not {"client_secret", "metadata_xml"} & set(provider_keys)
    assert check_rels(
        neo4j_session,
        "FireworksAccount",
        "id",
        "FireworksIdentityProvider",
        "display_name",
        "RESOURCE",
    ) == {(ACCOUNT_ID, "Okta"), (ACCOUNT_ID, "Google Workspace")}

    # Assert models and the deployment that serves an account-owned model
    assert check_nodes(
        neo4j_session,
        "FireworksModel",
        ["model_id", "kind", "public", "base_model"],
    ) == {
        (
            "reactor-assistant-lora",
            "HF_PEFT_ADDON",
            False,
            "accounts/fireworks/models/llama-v3p1-8b-instruct",
        ),
        ("donut-classifier", "HF_BASE_MODEL", True, None),
    }
    assert check_nodes(
        neo4j_session,
        "FireworksDeployment",
        ["deployment_id", "direct_route_type", "replica_count", "preemptible"],
    ) == {
        ("donut-prod", "INTERNET", 2, False),
        ("llama-lora", None, 0, True),
    }
    deployment_keys = neo4j_session.run(
        "MATCH (d:FireworksDeployment) "
        "UNWIND keys(d) AS key RETURN collect(DISTINCT key) AS keys",
    ).single()["keys"]
    assert "direct_route_api_keys" not in deployment_keys
    assert check_rels(
        neo4j_session,
        "FireworksDeployment",
        "deployment_id",
        "FireworksModel",
        "model_id",
        "SERVES",
    ) == {("donut-prod", "donut-classifier")}
    assert check_rels(
        neo4j_session,
        "FireworksAccount",
        "id",
        "FireworksDeployment",
        "deployment_id",
        "RESOURCE",
    ) == {(ACCOUNT_ID, "donut-prod"), (ACCOUNT_ID, "llama-lora")}

    # Assert datasets
    assert check_nodes(
        neo4j_session,
        "FireworksDataset",
        ["dataset_id", "example_count", "external_url", "created_by"],
    ) == {
        (
            "safety-manuals",
            1200,
            "gs://springfield-training/safety-manuals.jsonl",
            "mburns@springfield-nuclear.example",
        ),
    }
    assert check_rels(
        neo4j_session,
        "FireworksAccount",
        "id",
        "FireworksDataset",
        "dataset_id",
        "RESOURCE",
    ) == {(ACCOUNT_ID, "safety-manuals")}


def test_sync_fireworks_removes_stale_resources(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    with _fireworks_api():
        cartography.intel.fireworks.start_fireworks_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG),
        )
    remaining_users = [
        user
        for user in tests.data.fireworks.users.FIREWORKS_USERS
        if not user["name"].endswith("/hsimpson")
    ]
    remaining_keys = [
        key
        for key in tests.data.fireworks.apikeys.FIREWORKS_API_KEYS
        if key["keyId"] != "key_homer_default"
    ]

    # Act
    with _fireworks_api(
        users__get={"return_value": remaining_users},
        apikeys__get={"return_value": remaining_keys},
        deployments__get={
            "return_value": tests.data.fireworks.deployments.FIREWORKS_DEPLOYMENTS[:1],
        },
        secrets__get={"return_value": []},
    ):
        cartography.intel.fireworks.start_fireworks_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG_2),
        )

    # Assert
    assert check_nodes(neo4j_session, "FireworksUser", ["user_id"]) == {("mburns",)}
    assert check_nodes(neo4j_session, "FireworksApiKey", ["id"]) == {
        ("key_burns_admin",),
        ("key_ci_bot",),
    }
    assert check_nodes(neo4j_session, "FireworksDeployment", ["deployment_id"]) == {
        ("donut-prod",),
    }
    assert check_nodes(neo4j_session, "FireworksSecret", ["id"]) == set()


def test_sync_fireworks_keeps_keys_and_secrets_when_access_is_denied(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    with _fireworks_api():
        cartography.intel.fireworks.start_fireworks_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG),
        )

    # Act
    with _fireworks_api(
        apikeys__get={"side_effect": _http_error(403)},
        secrets__get={"side_effect": _http_error(403)},
        identityproviders__get={"side_effect": _http_error(403)},
        account__get_policy_settings={"return_value": ({}, False)},
    ):
        cartography.intel.fireworks.start_fireworks_ingestion(
            neo4j_session,
            _config(TEST_UPDATE_TAG_2),
        )

    # Assert a non-admin key leaves earlier results in place instead of deleting them
    assert check_nodes(neo4j_session, "FireworksApiKey", ["id", "lastupdated"]) == {
        ("key_burns_admin", TEST_UPDATE_TAG),
        ("key_homer_default", TEST_UPDATE_TAG),
        ("key_ci_bot", TEST_UPDATE_TAG),
    }
    assert len(check_nodes(neo4j_session, "FireworksSecret", ["id"])) == 2
    assert len(check_nodes(neo4j_session, "FireworksIdentityProvider", ["id"])) == 2
    # Unreadable policy settings clear the policy properties rather than keep stale ones
    assert check_nodes(
        neo4j_session,
        "FireworksAccount",
        ["policy_settings_readable", "residency", "zdr_inference_enforced"],
    ) == {(False, None, None)}
