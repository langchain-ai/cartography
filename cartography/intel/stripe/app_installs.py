import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.stripe.util import is_permission_error
from cartography.intel.stripe.util import list_v1
from cartography.models.stripe.app_install import StripeAppInstallSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        raw_installs = get(api_session)
    except requests.HTTPError as e:
        if not is_permission_error(e):
            raise
        logger.warning(
            "The Stripe API key can't read app installs; skipping them.",
        )
        return
    load_app_installs(
        neo4j_session,
        transform(raw_installs),
        common_job_parameters["STRIPE_ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session) -> list[dict[str, Any]]:
    return list_v1(api_session, "/v1/apps/installs")


def transform(installs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for install in installs:
        csp = install.get("content_security_policy_granted") or {}
        result.append(
            {
                "id": install["id"],
                "app_id": install["app"],
                "channel": install.get("channel"),
                "status": install.get("status"),
                "approval_required": install.get("approval_required"),
                "permissions_granted": install.get("permissions_granted"),
                "permissions_pending": install.get("permissions_pending"),
                "endpoints_granted": install.get("endpoints_granted"),
                "endpoints_pending": install.get("endpoints_pending"),
                "connect_src_granted": csp.get("connect_src"),
                "image_src_granted": csp.get("image_src"),
                "created_by": install.get("created_by"),
                "livemode": install.get("livemode"),
                "created": install.get("created"),
            },
        )
    return result


@timeit
def load_app_installs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        StripeAppInstallSchema(),
        data,
        lastupdated=update_tag,
        STRIPE_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        StripeAppInstallSchema(),
        common_job_parameters,
    ).run(neo4j_session)
