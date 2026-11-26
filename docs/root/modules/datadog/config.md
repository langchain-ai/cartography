# Datadog configuration

To sync a Datadog organization, give Cartography a read-only Datadog
credential. Cartography reads the organization, its users and service
accounts, its roles, which roles each account holds, and the permissions each
role grants. It sends only `GET` requests.

Cartography doesn't collect API keys, application keys, access tokens, or
logs. It identifies people only by their opaque Datadog user ID and doesn't
collect their email address or profile and sign-in details such as name,
title, MFA state, or last sign-in.

## Authentication

Cartography accepts two kinds of credentials. Both act with the permissions
of the service account that owns them, limited to the credential's scopes.

### Service account and scoped application key

1. In Datadog, go to **Organization Settings > Service Accounts**, and create a
   service account, for example `cartography-readonly`. Give it a role that
   grants `user_access_read`.
1. In the service account's side panel, create an application key, and limit
   it to the `user_access_read` scope. Datadog shows service account keys
   only once.
1. Create an API key for Cartography in **Organization Settings > API Keys**.
   Datadog requires an API key with every application key request.

An unscoped application key has every permission of its owner, so always
scope the key. Datadog only grants a scope that the owner's role also grants.

### Service access token

A service access token (SAT) belongs to a service account, has mandatory
scopes, can expire, and authenticates without an API key. Create one with
the `user_access_read` scope, and pass it in place of the application key.
Creating a SAT requires the `service_account_write` permission.

## Required permissions

`user_access_read` is the only permission and scope that the module needs.
Cartography calls these endpoints:

| API endpoint | Cartography data | Permission and scope |
| --- | --- | --- |
| `GET /api/v2/current_user` | `DatadogOrganization` | Any valid credential |
| `GET /api/v2/roles` | `DatadogRole` | `user_access_read` |
| `GET /api/v2/permissions` | `DatadogRole.permissions` | `user_access_read` |
| `GET /api/v2/users` | `DatadogUser`, `DatadogServiceAccount`, `HAS_ROLE` | `user_access_read` |

Every endpoint is required. If Datadog denies or fails a read, Cartography
stops the Datadog sync before it loads or cleans up that data, so existing
nodes stay in the graph.

## Configure Cartography

| CLI option | Description |
| --- | --- |
| `--datadog-app-key-env-var` | Name of the environment variable that holds the application key or service access token. If you omit this option or the variable is unset or empty, Cartography logs an info message and skips Datadog. |
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

- **`403` on `/api/v2/users`, `/api/v2/roles`, or `/api/v2/permissions`**: The
  credential lacks `user_access_read`, as a role permission or as a scope. The
  sync stops without changing Datadog nodes.
- **`DatadogIncompleteListError`**: A listing changed while Cartography paged
  through it, or Datadog's reported total didn't match the items returned.
  Cartography retries the listing up to three times and then stops without
  cleaning up. Rerun the sync.
- **`429`**: Datadog rate limits each endpoint per organization. Cartography
  retries throttled and `5xx` responses with exponential backoff and fails the
  sync without cleanup if retries run out.

## References

- [Datadog service accounts](https://docs.datadoghq.com/account_management/org_settings/service_accounts/)
- [Datadog API and application keys](https://docs.datadoghq.com/account_management/api-app-keys/)
- [Datadog role permissions](https://docs.datadoghq.com/account_management/rbac/permissions/)
- [Datadog users API](https://docs.datadoghq.com/api/latest/users/)
- [Datadog roles API](https://docs.datadoghq.com/api/latest/roles/)
