import logging

import neo4j

import cartography.intel.stripe.account
import cartography.intel.stripe.app_installs
import cartography.intel.stripe.connected_accounts
import cartography.intel.stripe.event_destinations
import cartography.intel.stripe.webhook_endpoints
from cartography.config import Config
from cartography.intel.stripe.util import build_session
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_stripe_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Stripe data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.stripe_api_key:
        logger.info(
            "Stripe import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = build_session(config.stripe_api_key)
    account_id = cartography.intel.stripe.account.sync(
        neo4j_session,
        api_session,
        config.update_tag,
    )
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "STRIPE_ACCOUNT_ID": account_id,
    }

    cartography.intel.stripe.webhook_endpoints.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.stripe.event_destinations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.stripe.app_installs.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    if config.stripe_sync_connected_accounts:
        cartography.intel.stripe.connected_accounts.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
        )
