from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.config import Config
from cartography.intel.stripe import start_stripe_ingestion
from tests.data.stripe.account import STRIPE_ACCOUNT
from tests.data.stripe.account import STRIPE_ACCOUNT_ID
from tests.data.stripe.app_installs import STRIPE_APP_INSTALLS
from tests.data.stripe.connected_accounts import STRIPE_CONNECTED_ACCOUNTS
from tests.data.stripe.event_destinations import STRIPE_EVENT_DESTINATIONS
from tests.data.stripe.event_destinations import TEST_AWS_ACCOUNT_ID
from tests.data.stripe.event_destinations import TEST_AZURE_SUBSCRIPTION_ID
from tests.data.stripe.webhook_endpoints import STRIPE_WEBHOOK_ENDPOINTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
API = "https://api.stripe.com"
NEXT_PAGE_URL = "/v2/core/event_destinations?page=page_2&limit=100"


def _ok(body: dict[str, Any]) -> Mock:
    return Mock(status_code=200, json=Mock(return_value=body), raise_for_status=Mock())


def _error(status_code: int, url: str) -> Mock:
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    return Mock(
        status_code=status_code,
        raise_for_status=Mock(side_effect=requests.HTTPError(response=response)),
    )


class FakeStripe:
    """Serve fixture pages the way the Stripe API paginates them."""

    def __init__(
        self,
        webhook_endpoints: list[Any] = STRIPE_WEBHOOK_ENDPOINTS,
        event_destinations: list[Any] = STRIPE_EVENT_DESTINATIONS,
        app_installs: list[Any] = STRIPE_APP_INSTALLS,
        connected_accounts: list[Any] = STRIPE_CONNECTED_ACCOUNTS,
        errors: dict[str, int] | None = None,
    ) -> None:
        self.v1_lists = {
            "/v1/webhook_endpoints": webhook_endpoints,
            "/v1/apps/installs": app_installs,
            "/v1/accounts": connected_accounts,
        }
        self.event_destinations = event_destinations
        self.errors = errors or {}

    def get(self, url: str, params: dict[str, Any] | None = None, **_: Any) -> Mock:
        path = url.removeprefix(API)
        params = params or {}
        if path in self.errors:
            return _error(self.errors[path], url)
        if path == "/v1/account":
            return _ok(STRIPE_ACCOUNT)
        if path in self.v1_lists:
            return _ok(self._v1_page(self.v1_lists[path], params))
        if path == "/v2/core/event_destinations":
            assert params["include[0]"] == "webhook_endpoint.url"
            if params.get("page") == "page_2":
                return _ok(
                    {"data": self.event_destinations[1:], "next_page_url": None},
                )
            return _ok(
                {
                    "data": self.event_destinations[:1],
                    "next_page_url": (
                        NEXT_PAGE_URL if len(self.event_destinations) > 1 else None
                    ),
                },
            )
        raise AssertionError(f"Unexpected Stripe request: {url}")

    @staticmethod
    def _v1_page(items: list[dict[str, Any]], params: dict[str, Any]) -> dict:
        start = 0
        if "starting_after" in params:
            ids = [item["id"] for item in items]
            start = ids.index(params["starting_after"]) + 1
        page = items[start : start + 1]
        return {"data": page, "has_more": start + 1 < len(items)}


def _sync(
    neo4j_session,
    fake: FakeStripe,
    update_tag: int = TEST_UPDATE_TAG,
    connected_accounts: bool = True,
) -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        stripe_api_key="rk_test_fake",
        stripe_sync_connected_accounts=connected_accounts,
    )
    with patch.object(requests.Session, "get", side_effect=fake.get):
        start_stripe_ingestion(neo4j_session, config)


def _list_property(neo4j_session, label: str, node_id: str, prop: str) -> list:
    return neo4j_session.run(
        f"MATCH (n:{label} {{id: $id}}) RETURN n.{prop} AS value",
        id=node_id,
    ).single()["value"]


def _reset(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        "MERGE (:AWSAccount {id: $aws}) MERGE (:AzureSubscription {id: $azure})",
        aws=TEST_AWS_ACCOUNT_ID,
        azure=TEST_AZURE_SUBSCRIPTION_ID,
    )


def test_sync_stripe(neo4j_session):
    # Arrange
    _reset(neo4j_session)

    # Act
    _sync(neo4j_session, FakeStripe())

    # Assert
    assert check_nodes(
        neo4j_session,
        "StripeAccount",
        [
            "id",
            "name",
            "display_name",
            "email",
            "decline_on_cvc_failure",
            "timezone",
        ],
    ) == {
        (
            STRIPE_ACCOUNT_ID,
            "Springfield Nuclear Power Plant",
            "SNPP",
            "billing@snpp.example.com",
            True,
            "America/Los_Angeles",
        ),
    }
    assert _list_property(
        neo4j_session, "StripeAccount", STRIPE_ACCOUNT_ID, "active_capabilities"
    ) == ["card_payments", "transfers"]
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name"]) >= {
        (STRIPE_ACCOUNT_ID, "Springfield Nuclear Power Plant"),
    }

    assert check_nodes(
        neo4j_session,
        "StripeWebhookEndpoint",
        ["id", "url", "host", "status", "application"],
    ) == {
        (
            "we_1Mr5jULkdIwHu7ix1ibLTM0x",
            "https://billing.snpp.example.com/stripe/webhook",
            "billing.snpp.example.com",
            "enabled",
            None,
        ),
        (
            "we_1PbGh2LkdIwHu7ixQ8Wl9yZe",
            "https://legacy.example.org:8443/hooks/stripe",
            "legacy.example.org",
            "disabled",
            "ca_FkyHCg7X8mlvCUdMDao4mMxagUfhIwXb",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "StripeEventDestination",
        ["id", "type", "status", "disabled_reason", "webhook_url"],
    ) == {
        (
            "ed_61RM8ltWcTW4mbsxf16RJyfa2xSQLHJJh1sxm7H0KVT6",
            "amazon_eventbridge",
            "enabled",
            None,
            None,
        ),
        (
            "ed_61RM8nqJdTW4mbsxf16RJyfa2xSQLHJJh1sxm7H0Kazg",
            "azure_event_grid",
            "disabled",
            "user",
            None,
        ),
        (
            "ed_61RM8pZbTTW4mbsxf16RJyfa2xSQLHJJh1sxm7H0Kbcd",
            "webhook_endpoint",
            "enabled",
            None,
            "https://ledger.snpp.example.com/stripe/thin",
        ),
    }
    assert _list_property(
        neo4j_session,
        "StripeEventDestination",
        "ed_61RM8ltWcTW4mbsxf16RJyfa2xSQLHJJh1sxm7H0KVT6",
        "events_from",
    ) == ["@self", "@accounts"]
    assert check_rels(
        neo4j_session,
        "StripeEventDestination",
        "id",
        "AWSAccount",
        "id",
        "DELIVERS_TO",
    ) == {("ed_61RM8ltWcTW4mbsxf16RJyfa2xSQLHJJh1sxm7H0KVT6", TEST_AWS_ACCOUNT_ID)}
    assert check_rels(
        neo4j_session,
        "StripeEventDestination",
        "id",
        "AzureSubscription",
        "id",
        "DELIVERS_TO",
    ) == {
        (
            "ed_61RM8nqJdTW4mbsxf16RJyfa2xSQLHJJh1sxm7H0Kazg",
            TEST_AZURE_SUBSCRIPTION_ID,
        ),
    }

    assert check_nodes(neo4j_session, "StripeAppInstall", ["id", "app_id"]) == {
        (
            "appinst_61VGZmT4pXc8Rk2w41LUZiLcTVChK7Ab",
            "app_61VGZkQ7mRbN3xPa41LUZiLcTVChQ9Ye",
        ),
    }
    assert _list_property(
        neo4j_session,
        "StripeAppInstall",
        "appinst_61VGZmT4pXc8Rk2w41LUZiLcTVChK7Ab",
        "permissions_granted",
    ) == ["customer_read", "event_read"]
    assert _list_property(
        neo4j_session,
        "StripeAppInstall",
        "appinst_61VGZmT4pXc8Rk2w41LUZiLcTVChK7Ab",
        "permissions_pending",
    ) == ["payment_intent_write"]
    assert check_nodes(neo4j_session, "ThirdPartyApp", ["id", "_ont_client_id"]) == {
        (
            "appinst_61VGZmT4pXc8Rk2w41LUZiLcTVChK7Ab",
            "app_61VGZkQ7mRbN3xPa41LUZiLcTVChQ9Ye",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "StripeConnectedAccount",
        [
            "id",
            "name",
            "controller_type",
            "controller_stripe_dashboard_type",
            "disabled_reason",
        ],
    ) == {
        ("acct_1Ocw2xPZ3dLy0kaj", "Kwik-E-Mart", "application", "express", None),
        (
            "acct_1PdTq8RQ7aW2nfE5",
            None,
            "account",
            "full",
            "requirements.past_due",
        ),
    }

    for label in (
        "StripeWebhookEndpoint",
        "StripeEventDestination",
        "StripeAppInstall",
        "StripeConnectedAccount",
    ):
        assert {
            account_id
            for account_id, _ in check_rels(
                neo4j_session, "StripeAccount", "id", label, "id", "RESOURCE"
            )
        } == {STRIPE_ACCOUNT_ID}, label


def test_sync_stripe_stores_no_secrets_or_pii(neo4j_session):
    # Arrange
    _reset(neo4j_session)

    # Act
    _sync(neo4j_session, FakeStripe())

    # Assert
    keys = neo4j_session.run(
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label STARTS WITH 'Stripe')
        UNWIND keys(n) AS key
        RETURN collect(DISTINCT key) AS keys
        """,
    ).single()["keys"]
    assert not {
        "auth_code",
        "secret",
        "signing_secret",
        "metadata",
        "tos_acceptance",
        "individual",
        "company",
        "external_accounts",
    } & set(keys)
    assert check_nodes(neo4j_session, "StripeConnectedAccount", ["email"]) == {
        (None,),
    }


def test_sync_stripe_removes_stale_resources(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _sync(neo4j_session, FakeStripe())

    # Act
    _sync(
        neo4j_session,
        FakeStripe(
            webhook_endpoints=STRIPE_WEBHOOK_ENDPOINTS[:1],
            event_destinations=STRIPE_EVENT_DESTINATIONS[2:],
            app_installs=[],
            connected_accounts=STRIPE_CONNECTED_ACCOUNTS[:1],
        ),
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert
    assert check_nodes(neo4j_session, "StripeWebhookEndpoint", ["id"]) == {
        ("we_1Mr5jULkdIwHu7ix1ibLTM0x",),
    }
    assert check_nodes(neo4j_session, "StripeEventDestination", ["id"]) == {
        ("ed_61RM8pZbTTW4mbsxf16RJyfa2xSQLHJJh1sxm7H0Kbcd",),
    }
    assert check_nodes(neo4j_session, "StripeAppInstall", ["id"]) == set()
    assert check_nodes(neo4j_session, "StripeConnectedAccount", ["id"]) == {
        ("acct_1Ocw2xPZ3dLy0kaj",),
    }


def test_sync_stripe_keeps_resources_a_key_cannot_read(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    _sync(neo4j_session, FakeStripe())

    # Act
    _sync(
        neo4j_session,
        FakeStripe(
            errors={
                "/v1/webhook_endpoints": 403,
                "/v2/core/event_destinations": 403,
                "/v1/apps/installs": 403,
            },
        ),
        update_tag=TEST_UPDATE_TAG + 1,
        connected_accounts=False,
    )

    # Assert
    assert check_nodes(neo4j_session, "StripeWebhookEndpoint", ["lastupdated"]) == {
        (TEST_UPDATE_TAG,),
    }
    assert check_nodes(neo4j_session, "StripeEventDestination", ["lastupdated"]) == {
        (TEST_UPDATE_TAG,),
    }
    assert check_nodes(neo4j_session, "StripeAppInstall", ["lastupdated"]) == {
        (TEST_UPDATE_TAG,),
    }
    assert check_nodes(neo4j_session, "StripeAccount", ["lastupdated"]) == {
        (TEST_UPDATE_TAG + 1,),
    }


@pytest.mark.parametrize(
    "path",
    ["/v1/account", "/v1/webhook_endpoints", "/v2/core/event_destinations"],
)
def test_sync_stripe_raises_on_other_errors(path, neo4j_session):
    # Arrange
    _reset(neo4j_session)
    status_code = 403 if path == "/v1/account" else 401

    # Act and assert
    with pytest.raises(requests.HTTPError):
        _sync(neo4j_session, FakeStripe(errors={path: status_code}))


def test_sync_stripe_skips_when_unconfigured(neo4j_session):
    # Arrange
    _reset(neo4j_session)
    config = Config(neo4j_uri="bolt://localhost:7687", update_tag=TEST_UPDATE_TAG)

    # Act
    with patch.object(requests.Session, "get") as get:
        start_stripe_ingestion(neo4j_session, config)

    # Assert
    get.assert_not_called()
    assert check_nodes(neo4j_session, "StripeAccount", ["id"]) == set()
