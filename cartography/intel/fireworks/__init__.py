import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.fireworks.account
import cartography.intel.fireworks.apikeys
import cartography.intel.fireworks.datasets
import cartography.intel.fireworks.deployments
import cartography.intel.fireworks.identityproviders
import cartography.intel.fireworks.models
import cartography.intel.fireworks.secrets
import cartography.intel.fireworks.users
from cartography.config import Config
from cartography.intel.fireworks.util import BASE_URL
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_fireworks_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Fireworks AI data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.fireworks_apikey or not config.fireworks_account_id:
        logger.info(
            "Fireworks AI import is not configured - skipping this module. "
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
    api_session.headers.update(
        {"Authorization": f"Bearer {config.fireworks_apikey}"},
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": BASE_URL,
        "ACCOUNT_ID": config.fireworks_account_id,
    }

    cartography.intel.fireworks.account.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    # API keys link to their owners, so users and service accounts load first.
    cartography.intel.fireworks.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.fireworks.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.fireworks.secrets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.fireworks.identityproviders.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    # Deployments link to the models they serve, so models load first.
    cartography.intel.fireworks.models.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.fireworks.deployments.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.fireworks.datasets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
