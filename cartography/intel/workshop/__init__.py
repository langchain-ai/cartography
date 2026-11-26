import logging

import neo4j

from cartography.config import Config
from cartography.intel.workshop.sync_settings import sync
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_workshop_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not all(
        (config.workshop_api_url, config.workshop_api_key, config.workshop_tenant_id),
    ):
        logger.info("Workshop is not configured - skipping module")
        return
    sync(
        neo4j_session,
        config.workshop_api_url,
        config.workshop_api_key,
        config.workshop_tenant_id,
        config.update_tag,
    )
