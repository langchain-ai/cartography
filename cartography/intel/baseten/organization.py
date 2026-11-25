from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.baseten.util import get_json
from cartography.models.baseten.organization import BasetenOrganizationSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> dict[str, Any]:
    organization = transform(
        get(api_session, common_job_parameters["BASE_URL"]),
    )
    load_organization(
        neo4j_session,
        organization,
        common_job_parameters["UPDATE_TAG"],
    )
    return organization


@timeit
def get(api_session: requests.Session, base_url: str) -> dict[str, Any]:
    return get_json(api_session, f"{base_url}/v1/organizations/me")


def transform(organization: dict[str, Any]) -> dict[str, Any]:
    aws_assume_role = organization.get("aws_assume_role")
    return {
        "org_id": organization["org_id"],
        "name": organization.get("name"),
        "created_at": organization.get("created_at"),
        "allow_personal_api_keys": organization.get("allow_personal_api_keys"),
        "allow_service_account_api_keys": organization.get(
            "allow_service_account_api_keys",
        ),
        "allow_team_admins_to_manage_roles": organization.get(
            "allow_team_admins_to_manage_roles",
        ),
        "aws_assume_role_enabled": aws_assume_role is not None,
        "aws_assume_role_baseten_role_arn": (
            aws_assume_role.get("baseten_role_arn") if aws_assume_role else None
        ),
    }


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    organization: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BasetenOrganizationSchema(),
        [organization],
        lastupdated=update_tag,
    )
