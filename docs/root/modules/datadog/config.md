# Datadog configuration

To sync a Datadog organization, give Cartography a read-only Datadog
credential. Cartography reads the organization, its users, service accounts,
and roles, and the metadata of its API keys, application keys, and access
tokens. It sends only `GET` requests, and it never reads a key or token value.

## Authentication

Cartography accepts two kinds of credentials. Both act with the permissions
of the user or service account that owns them, limited to the credential's
scopes.

### Service account and scoped application key

1. In Datadog, go to **Organization Settings > Service Accounts**, and create a
   service account, for example `cartography-readonly`. Give it a role that
   grants the permissions in [Required permissions](#required-permissions).
1. In the service account's side panel, create an application key, and limit
   it to these scopes: `user_access_read`, `api_keys_read`, and
   `org_app_keys_read`. Datadog shows service account keys only once.
1. Create an API key for Cartography in **Organization Settings > API Keys**.
   Datadog requires an API key with every application key request.

An unscoped application key has every permission of its owner, so always
scope the key. Datadog only grants a scope that the owner's role also grants.

### Service access token

A service access token (SAT) belongs to a service account, has mandatory
scopes, can expire, and authenticates without an API key. Create one for the
service account with the scopes listed earlier, and pass it in place of the
application key. Creating a SAT requires the `service_account_write`
permission.

## Required permissions

Cartography calls these endpoints. A failure on a required endpoint stops the
Datadog sync before it changes any data of that type.

| API endpoint | Cartography data | Permission and scope |
| --- | --- | --- |
| `GET /api/v2/current_user` | `DatadogOrganization` | Any valid credential |
| `GET /api/v2/roles` | `DatadogRole` | `user_access_read` |
| `GET /api/v2/permissions` | `DatadogRole.permissions` | `user_access_read` |
| `GET /api/v2/users` | `DatadogUser`, `DatadogServiceAccount`, `HAS_ROLE` | `user_access_read` |

## Optional permissions

When the credential lacks one of these permissions, Datadog answers `403`.
Cartography logs a warning, skips that data type, and leaves its existing
nodes unchanged instead of deleting them.

| API endpoint | Cartography data | Permission and scope |
| --- | --- | --- |
| `GET /api/v2/api_keys` | `DatadogAPIKey`, `CREATED` | `api_keys_read` |
| `GET /api/v2/application_keys` | `DatadogApplicationKey`, `OWNED_BY` | `org_app_keys_read` |
| `GET /api/v2/personal_access_tokens` | `DatadogAccessToken`, `OWNED_BY` | `org_app_keys_read` |

The access token listing also accepts `user_app_keys`, which may return only
the caller's tokens. To avoid cleaning up from that partial listing,
Cartography reads access tokens only after the organization-wide application
key listing succeeds, which proves `org_app_keys_read`.

:::{note}
The list endpoints don't return key values, and Cartography never calls the
single-key endpoints. The permissions themselves are broader: `api_keys_read`
also allows `GET /api/v2/api_keys/{id}`, which returns the API key value, and
`org_app_keys_read` can expose application key values when One-Time Read mode
is off. Store the Cartography credential as a secret, enable One-Time Read
mode, and omit `api_keys_read` or `org_app_keys_read` if you don't need key
inventory.
:::

## Configure Cartography

| CLI option | Description |
| --- | --- |
| `--datadog-app-key-env-var` | Name of the environment variable that holds the application key, personal access token, or service access token. If you omit this option or the variable is unset or empty, Cartography logs an info message and skips Datadog. |
| `--datadog-api-key-env-var` | Name of the environment variable that holds the API key. Required with an application key. Omit it with an access token. |
| `--datadog-site` | Datadog site of the organization. Defaults to `datadoghq.com`. Other values include `us3.datadoghq.com`, `us5.datadoghq.com`, `datadoghq.eu`, `ap1.datadoghq.com`, and `ddog-gov.com`. A value that starts with `https://` is used as the API base URL. |

## Run Cartography

```bash
export DD_API_KEY="..."
export DD_APP_KEY="..."
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules datadog \
  --datadog-site datadoghq.com \
  --datadog-api-key-env-var DD_API_KEY \
  --datadog-app-key-env-var DD_APP_KEY
```

## Advanced configuration

Each credential reads one organization. To sync several organizations, such
as a parent and its child organizations, run Cartography once per
organization with that organization's credential. Cleanup is scoped to the
organization, so one organization's sync never deletes another's nodes.

## Troubleshooting

- **`403` on `/api/v2/users` or `/api/v2/roles`**: The credential lacks
  `user_access_read`, as a role permission or as a scope.
- **`403` warnings for keys or tokens**: The credential lacks `api_keys_read`
  or `org_app_keys_read`. The sync continues without that data.
- **`DatadogIncompleteListError`**: A listing changed while Cartography paged
  through it, or Datadog's reported total didn't match the items returned.
  Cartography retries the listing up to three times and then stops without
  cleaning up. Rerun the sync.
- **`429`**: Datadog rate limits each endpoint per organization. Cartography
  retries throttled and `5xx` responses with exponential backoff and fails the
  sync without cleanup if retries run out.

## References

- [Datadog API and application keys](https://docs.datadoghq.com/account_management/api-app-keys/)
- [Datadog service accounts](https://docs.datadoghq.com/account_management/org_settings/service_accounts/)
- [Datadog personal access tokens](https://docs.datadoghq.com/account_management/personal-access-tokens/)
- [Datadog role permissions](https://docs.datadoghq.com/account_management/rbac/permissions/)
- [Datadog key management API](https://docs.datadoghq.com/api/latest/key-management/)
