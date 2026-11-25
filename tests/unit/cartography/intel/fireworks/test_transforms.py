import cartography.intel.fireworks.account
import cartography.intel.fireworks.deployments
import cartography.intel.fireworks.identityproviders
import tests.data.fireworks.account
import tests.data.fireworks.deployments
import tests.data.fireworks.identityproviders

ACCOUNT = tests.data.fireworks.account.FIREWORKS_ACCOUNT
ACCOUNT_ID = tests.data.fireworks.account.FIREWORKS_ACCOUNT_ID


def test_account_without_saved_policy_settings_gets_documented_defaults():
    # Act
    result = cartography.intel.fireworks.account.transform(
        ACCOUNT, {}, True, ACCOUNT_ID
    )

    # Assert
    assert result["policy_settings_readable"] is True
    assert result["residency"] is None
    assert result["cmek_required"] is False
    assert result["zdr_default_enforced"] is False
    assert result["zdr_inference_enforced"] is False
    assert result["zdr_training_enforced"] is False
    assert result["default_allow_serverless"] is True
    assert result["default_allow_training"] is True
    assert result["model_access_rule_count"] == 0


def test_account_zdr_scopes_inherit_the_default_unless_overridden():
    # Act
    result = cartography.intel.fireworks.account.transform(
        ACCOUNT,
        {
            "zeroDataRetention": {
                "defaultEnforced": False,
                "inference": {"enforcement": "ENFORCED"},
                "training": {"enforcement": "ENFORCEMENT_UNSPECIFIED"},
            },
        },
        True,
        ACCOUNT_ID,
    )

    # Assert
    assert result["zdr_inference_enforcement"] == "ENFORCED"
    assert result["zdr_inference_enforced"] is True
    assert result["zdr_training_enforcement"] is None
    assert result["zdr_training_enforced"] is False


def test_account_with_unreadable_policy_settings_has_no_policy_properties():
    # Act
    result = cartography.intel.fireworks.account.transform(
        ACCOUNT, {}, False, ACCOUNT_ID
    )

    # Assert
    assert result["policy_settings_readable"] is False
    assert "zdr_inference_enforced" not in result
    assert "default_allow_serverless" not in result


def test_deployment_transform_drops_direct_route_api_keys():
    # Act
    results = cartography.intel.fireworks.deployments.transform(
        tests.data.fireworks.deployments.FIREWORKS_DEPLOYMENTS,
    )

    # Assert
    for result in results:
        assert "fw_direct_route_secret_value" not in result.values()
        assert not any("api_key" in key for key in result)


def test_identity_provider_transform_drops_secrets():
    # Act
    results = cartography.intel.fireworks.identityproviders.transform(
        tests.data.fireworks.identityproviders.FIREWORKS_IDENTITY_PROVIDERS,
    )

    # Assert
    serialized = repr(results)
    assert "oidc-client-secret-value" not in serialized
    assert "EntityDescriptor" not in serialized
    assert {result["protocol"] for result in results} == {"SAML", "OIDC"}
