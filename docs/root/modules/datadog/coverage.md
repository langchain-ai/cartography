# Datadog coverage and sync safety

The Datadog module covers identity and credential governance: who has access
to the organization, through which roles, and which credentials exist and who
owns them. This page lists what the module reads, how it protects existing
graph data, and what it doesn't cover.

## Sync safety

Cartography deletes stale Datadog nodes only after it reads a complete listing
of that node type:

- **Complete listings only**: Each list endpoint is read 100 items per page.
  Every page must report the same total in `meta.page`, no item may appear on
  two pages, and the item count must match the total. Otherwise, Cartography
  retries the whole listing up to three times and then raises
  `DatadogIncompleteListError` before it loads or cleans up anything of that
  type.
- **Errors stop cleanup**: HTTP errors, exhausted `429` or `5xx` retries, and
  timeouts propagate, so the cleanup for that type and every later type never
  runs.
- **Empty required listings fail**: The credential's own user and the managed
  roles always exist, so an empty user or role listing raises instead of
  deleting every user or role.
- **Missing optional permissions keep data**: A `403` on an optional listing
  skips both its load and its cleanup, so earlier nodes stay in the graph with
  their previous `lastupdated` value.
- **Organization scope**: Cleanup only touches nodes attached to the
  organization that the credential belongs to.
- **Read-only client**: The HTTP session refuses every method except `GET`.

## Secrets

Cartography never stores a secret. API keys and application keys keep only
their ID, name, and last four characters. Access tokens keep neither their
secret nor their public portion. Transforms copy an explicit list of fields,
so a key value that an endpoint returned unexpectedly is dropped.

## Coverage gaps

The module doesn't read these Datadog resources yet:

| Resource | Endpoint | Why it matters |
| --- | --- | --- |
| Teams and team memberships | `GET /api/v2/team` (`teams_read`) | Teams grant team-scoped roles and own resources. |
| SAML role mappings | `GET /api/v2/authn_mappings` (`user_access_read`) | Mappings assign roles from identity provider attributes. Users' resulting roles are still synced. |
| Organization login settings | `GET /api/v1/org/{public_id}` | SAML strict mode and default login methods. The API reference doesn't list the required permission. |
| Restriction policies | `GET /api/v2/restriction_policy/{resource_id}` | Per-resource access grants on dashboards, monitors, and other objects. There's no list endpoint, so each resource must be read separately. |
| Logs restriction queries | `GET /api/v2/logs/config/restriction_queries` (`logs_read_config`) | Limits which logs each role can read. |

API and permission limits:

- **Managed roles**: The API doesn't flag managed roles, and role names aren't
  unique, so `DatadogRole` doesn't record whether a role is built in.
- **MFA**: `mfa_enabled` covers only Datadog's own MFA. MFA enforced by a SAML
  identity provider isn't visible.
- **Sign-in and usage times**: `last_login_time`, `date_last_used`, and
  `last_used_at` are `null` when Datadog omits them.
- **Leak detection**: `leaked` is `null` when a response doesn't include
  `leak_information`.
- **API key ownership**: API keys belong to the organization. Datadog reports
  only the creator and last modifier, so `CREATED` links the creator, not an
  owner.
- **Per-service-account endpoints**: `GET /api/v2/service_accounts/{id}/application_keys`
  and `.../access_tokens` require the write permission `service_account_write`.
  Cartography uses the organization-wide listings instead, which include keys
  and tokens owned by service accounts.
- **Other organizations**: A user's memberships in other organizations aren't
  synced. Run Cartography with a credential from each organization.
