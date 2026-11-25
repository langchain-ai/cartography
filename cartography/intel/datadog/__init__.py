import logging

import neo4j

import cartography.intel.datadog.accesstokens
import cartography.intel.datadog.apikeys
import cartography.intel.datadog.applicationkeys
import cartography.intel.datadog.organization
import cartography.intel.datadog.roles
import cartography.intel.datadog.users
from cartography.config import Config
from cartography.intel.datadog.util import build_base_url
from cartography.intel.datadog.util import build_session
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_datadog_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform read-only ingestion of Datadog
    governance data. Otherwise warn and exit.

    Each resource type is cleaned up only after Cartography reads its complete
    listing. A failed, throttled, or inconsistent read raises before cleanup,
    and an optional listing that the credential can't read is skipped without
    cleanup, so existing nodes stay in the graph.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.datadog_app_key:
        logger.info(
            "Datadog import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    base_url = build_base_url(config.datadog_site)
    api_session = build_session(config.datadog_api_key, config.datadog_app_key)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    org_id = cartography.intel.datadog.organization.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    common_job_parameters["ORG_ID"] = org_id

    # Roles load before users so that HAS_ROLE edges find their targets, and
    # users load before keys so that ownership edges find theirs.
    cartography.intel.datadog.roles.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    cartography.intel.datadog.users.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    cartography.intel.datadog.apikeys.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    org_app_keys_readable = cartography.intel.datadog.applicationkeys.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    if org_app_keys_readable:
        cartography.intel.datadog.accesstokens.sync(
            neo4j_session,
            api_session,
            base_url,
            common_job_parameters,
        )
