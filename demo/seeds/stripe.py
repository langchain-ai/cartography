from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.stripe.account
import cartography.intel.stripe.app_installs
import cartography.intel.stripe.connected_accounts
import cartography.intel.stripe.event_destinations
import cartography.intel.stripe.webhook_endpoints
import tests.data.stripe.account
import tests.data.stripe.app_installs
import tests.data.stripe.connected_accounts
import tests.data.stripe.event_destinations
import tests.data.stripe.webhook_endpoints
from demo.seeds.base import Seed


class StripeSeed(Seed):
    @patch.object(
        cartography.intel.stripe.account,
        "get",
        return_value=tests.data.stripe.account.STRIPE_ACCOUNT,
    )
    @patch.object(
        cartography.intel.stripe.webhook_endpoints,
        "get",
        return_value=tests.data.stripe.webhook_endpoints.STRIPE_WEBHOOK_ENDPOINTS,
    )
    @patch.object(
        cartography.intel.stripe.event_destinations,
        "get",
        return_value=tests.data.stripe.event_destinations.STRIPE_EVENT_DESTINATIONS,
    )
    @patch.object(
        cartography.intel.stripe.app_installs,
        "get",
        return_value=tests.data.stripe.app_installs.STRIPE_APP_INSTALLS,
    )
    @patch.object(
        cartography.intel.stripe.connected_accounts,
        "get",
        return_value=tests.data.stripe.connected_accounts.STRIPE_CONNECTED_ACCOUNTS,
    )
    def seed(self, *args) -> None:
        api_session = Mock()
        account_id = cartography.intel.stripe.account.sync(
            self.neo4j_session,
            api_session,
            self.update_tag,
        )
        common_job_parameters = {
            "UPDATE_TAG": self.update_tag,
            "STRIPE_ACCOUNT_ID": account_id,
        }
        for module in (
            cartography.intel.stripe.webhook_endpoints,
            cartography.intel.stripe.event_destinations,
            cartography.intel.stripe.app_installs,
            cartography.intel.stripe.connected_accounts,
        ):
            module.sync(self.neo4j_session, api_session, common_job_parameters)
