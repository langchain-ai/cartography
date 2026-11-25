import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.stripe.account import transform_account_fields
from cartography.intel.stripe.util import list_v1
from cartography.models.stripe.connected_account import StripeConnectedAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    accounts = transform(get(api_session))
    load_connected_accounts(
        neo4j_session,
        accounts,
        common_job_parameters["STRIPE_ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session) -> list[dict[str, Any]]:
    return list_v1(api_session, "/v1/accounts")


def transform(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for account in accounts:
        controller = account.get("controller") or {}
        item = transform_account_fields(account)
        item["controller_is_controller"] = controller.get("is_controller")
        item["controller_requirement_collection"] = controller.get(
            "requirement_collection"
        )
        item["controller_fees_payer"] = (controller.get("fees") or {}).get("payer")
        item["controller_losses_payments"] = (controller.get("losses") or {}).get(
            "payments"
        )
        item["controller_stripe_dashboard_type"] = (
            controller.get("stripe_dashboard") or {}
        ).get("type")
        result.append(item)
    return result


@timeit
def load_connected_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        StripeConnectedAccountSchema(),
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
        StripeConnectedAccountSchema(),
        common_job_parameters,
    ).run(neo4j_session)
