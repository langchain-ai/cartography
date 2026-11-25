from unittest.mock import Mock
from unittest.mock import patch

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
from cartography.intel.fireworks.util import BASE_URL
from demo.seeds.base import Seed

ACCOUNT_ID = tests.data.fireworks.account.FIREWORKS_ACCOUNT_ID


class FireworksSeed(Seed):
    @patch.object(
        cartography.intel.fireworks.account,
        "get",
        return_value=tests.data.fireworks.account.FIREWORKS_ACCOUNT,
    )
    @patch.object(
        cartography.intel.fireworks.account,
        "get_policy_settings",
        return_value=(tests.data.fireworks.account.FIREWORKS_POLICY_SETTINGS, True),
    )
    @patch.object(
        cartography.intel.fireworks.users,
        "get",
        return_value=tests.data.fireworks.users.FIREWORKS_USERS,
    )
    @patch.object(
        cartography.intel.fireworks.apikeys,
        "get",
        return_value=tests.data.fireworks.apikeys.FIREWORKS_API_KEYS,
    )
    @patch.object(
        cartography.intel.fireworks.secrets,
        "get",
        return_value=tests.data.fireworks.secrets.FIREWORKS_SECRETS,
    )
    @patch.object(
        cartography.intel.fireworks.identityproviders,
        "get",
        return_value=tests.data.fireworks.identityproviders.FIREWORKS_IDENTITY_PROVIDERS,
    )
    @patch.object(
        cartography.intel.fireworks.models,
        "get",
        return_value=tests.data.fireworks.models.FIREWORKS_MODELS,
    )
    @patch.object(
        cartography.intel.fireworks.deployments,
        "get",
        return_value=tests.data.fireworks.deployments.FIREWORKS_DEPLOYMENTS,
    )
    @patch.object(
        cartography.intel.fireworks.datasets,
        "get",
        return_value=tests.data.fireworks.datasets.FIREWORKS_DATASETS,
    )
    def seed(self, *args) -> None:
        api_session = Mock()
        common_job_parameters = {
            "UPDATE_TAG": self.update_tag,
            "BASE_URL": BASE_URL,
            "ACCOUNT_ID": ACCOUNT_ID,
        }
        for module in (
            cartography.intel.fireworks.account,
            cartography.intel.fireworks.users,
            cartography.intel.fireworks.apikeys,
            cartography.intel.fireworks.secrets,
            cartography.intel.fireworks.identityproviders,
            cartography.intel.fireworks.models,
            cartography.intel.fireworks.deployments,
            cartography.intel.fireworks.datasets,
        ):
            module.sync(self.neo4j_session, api_session, common_job_parameters)
