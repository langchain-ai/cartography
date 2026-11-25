import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.baseten.apikeys
import cartography.intel.baseten.chains
import cartography.intel.baseten.environment_groups
import cartography.intel.baseten.models
import cartography.intel.baseten.organization
import cartography.intel.baseten.secrets
import cartography.intel.baseten.teams
import cartography.intel.baseten.users
from cartography.config import Config
from cartography.intel.baseten.util import BASE_URL
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_baseten_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Baseten data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.baseten_api_key:
        logger.info(
            "Baseten import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {config.baseten_api_key}"})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": BASE_URL,
    }

    organization = cartography.intel.baseten.organization.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    common_job_parameters["ORG_ID"] = organization["org_id"]
    logger.info(
        "Syncing Baseten organization %s (%s)",
        organization.get("name"),
        organization["org_id"],
    )

    teams = cartography.intel.baseten.teams.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    team_ids_by_name = {team["name"]: team["id"] for team in teams}

    # Users and models are loaded before API keys and environment groups, which link
    # to them.
    cartography.intel.baseten.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.baseten.models.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        team_ids_by_name,
    )
    cartography.intel.baseten.chains.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        team_ids_by_name,
    )
    cartography.intel.baseten.secrets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        teams,
    )
    cartography.intel.baseten.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        team_ids_by_name,
    )
    cartography.intel.baseten.environment_groups.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        teams,
    )
