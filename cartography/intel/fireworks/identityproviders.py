import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.fireworks.util import is_access_denied
from cartography.intel.fireworks.util import paginated_get
from cartography.models.fireworks.identityprovider import (
    FireworksIdentityProviderSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    account_id = common_job_parameters["ACCOUNT_ID"]
    try:
        raw_providers = get(api_session, common_job_parameters["BASE_URL"], account_id)
    except requests.HTTPError as e:
        if not is_access_denied(e):
            raise
        logger.warning(
            "Fireworks AI API key cannot list identity providers in account %s; "
            "custom SSO needs an Enterprise account. Skipping identity providers.",
            account_id,
        )
        return
    providers = transform(raw_providers)
    logger.info(
        "Loading %d Fireworks AI identity providers for account %s",
        len(providers),
        account_id,
    )
    load_identity_providers(
        neo4j_session,
        providers,
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/accounts/{account_id}/identityProviders",
        "identityProviders",
    )


def transform(raw_providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # `oidcConfig.clientSecret` and `samlConfig.metadataXml` are deliberately not copied.
    providers: list[dict[str, Any]] = []
    for raw in raw_providers:
        saml = raw.get("samlConfig") or {}
        oidc = raw.get("oidcConfig") or {}
        if raw.get("samlConfig") is not None:
            protocol: str | None = "SAML"
            issuer = saml.get("metadataUrl")
        elif raw.get("oidcConfig") is not None:
            protocol = "OIDC"
            issuer = oidc.get("issuerUrl") or raw.get("issuerUrl")
        else:
            protocol = None
            issuer = raw.get("issuerUrl")
        providers.append(
            {
                "id": raw["name"],
                "display_name": raw.get("displayName"),
                "protocol": protocol,
                "issuer": issuer,
                "client_id": oidc.get("clientId") or raw.get("clientId"),
                "saml_email_attribute": saml.get("samlEmailAttribute"),
                "tenant_domains": raw.get("tenantDomains"),
                "domain_url": raw.get("domainUrl"),
                "enforce_sso": raw.get("enforceSso"),
                "enable_jit_user_provisioning": raw.get("enableJitUserProvisioning"),
                "jit_default_role": raw.get("jitDefaultRole"),
                "enable_idp_initiated_sso": raw.get("enableIdpInitiatedSso"),
                "state": raw.get("state"),
                "create_time": raw.get("createTime"),
                "update_time": raw.get("updateTime"),
            },
        )
    return providers


@timeit
def load_identity_providers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FireworksIdentityProviderSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        FireworksIdentityProviderSchema(),
        common_job_parameters,
    ).run(neo4j_session)
