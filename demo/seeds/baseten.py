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
from demo.seeds.base import Seed


class BasetenSeed(Seed):
    @patch.object(
        cartography.intel.baseten.environment_groups,
        "get",
        return_value=[
            group
            for body in tests.data.baseten.environment_groups.BASETEN_ENVIRONMENT_GROUPS_BY_TEAM.values()
            for group in body["items"]
        ],
    )
    @patch.object(
        cartography.intel.baseten.apikeys,
        "get",
        return_value=tests.data.baseten.apikeys.BASETEN_API_KEYS["keys"],
    )
    @patch.object(
        cartography.intel.baseten.secrets,
        "get",
        return_value=tests.data.baseten.secrets.BASETEN_SECRETS_BY_TEAM,
    )
    @patch.object(
        cartography.intel.baseten.chains,
        "get",
        return_value=tests.data.baseten.chains.BASETEN_CHAINS["chains"],
    )
    @patch.object(
        cartography.intel.baseten.models,
        "get_deployments",
        return_value=[
            deployment
            for body in tests.data.baseten.models.BASETEN_DEPLOYMENTS.values()
            for deployment in body["deployments"]
        ],
    )
    @patch.object(
        cartography.intel.baseten.models,
        "get",
        return_value=tests.data.baseten.models.BASETEN_MODELS["models"],
    )
    @patch.object(
        cartography.intel.baseten.users,
        "get",
        return_value=tests.data.baseten.users.BASETEN_USERS,
    )
    @patch.object(
        cartography.intel.baseten.teams,
        "get",
        return_value=tests.data.baseten.teams.BASETEN_TEAMS["teams"],
    )
    @patch.object(
        cartography.intel.baseten.organization,
        "get",
        return_value=tests.data.baseten.organization.BASETEN_ORGANIZATION,
    )
    def seed(self, *args) -> None:
        cartography.intel.baseten.start_baseten_ingestion(
            self.neo4j_session,
            Config(
                neo4j_uri="bolt://localhost:7687",
                update_tag=self.update_tag,
                baseten_api_key="demo",
            ),
        )
