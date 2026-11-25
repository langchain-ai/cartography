import pytest

from cartography.intel.stripe import account
from cartography.intel.stripe import app_installs
from cartography.intel.stripe import connected_accounts
from cartography.intel.stripe.util import sanitize_url
from tests.data.stripe.account import STRIPE_ACCOUNT
from tests.data.stripe.app_installs import STRIPE_APP_INSTALLS
from tests.data.stripe.connected_accounts import STRIPE_CONNECTED_ACCOUNTS


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://hooks.example.com/stripe?token=s3cr3t#frag",
            ("https://hooks.example.com/stripe", "hooks.example.com"),
        ),
        (
            "https://user:pass@hooks.example.com:8443/stripe",
            ("https://hooks.example.com:8443/stripe", "hooks.example.com"),
        ),
        (None, (None, None)),
    ],
)
def test_sanitize_url_drops_credentials_query_and_fragment(url, expected):
    # Act and assert
    assert sanitize_url(url) == expected


def test_account_name_falls_back_to_display_name_then_id():
    # Arrange
    no_business_name = {
        **STRIPE_ACCOUNT,
        "business_profile": {"name": None},
    }
    no_names = {**no_business_name, "settings": {}}

    # Act
    with_display_name = account.transform(no_business_name)
    with_id = account.transform(no_names)

    # Assert
    assert with_display_name["name"] == "SNPP"
    assert with_id["name"] == STRIPE_ACCOUNT["id"]


def test_connected_accounts_drop_email_and_legal_entity_data():
    # Act
    result = connected_accounts.transform(STRIPE_CONNECTED_ACCOUNTS)

    # Assert
    for item in result:
        assert not {"email", "individual", "company", "tos_acceptance"} & set(item)
    assert result[0]["active_capabilities"] == ["card_payments"]


def test_app_installs_drop_auth_code():
    # Act
    result = app_installs.transform(STRIPE_APP_INSTALLS)

    # Assert
    assert "auth_code" not in result[0]
    assert "ac_do_not_store" not in result[0].values()
