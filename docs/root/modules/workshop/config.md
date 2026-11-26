# Workshop configuration

This connector reads workstation inventory, host tags, directory users, the tag catalog,
and configured tag-to-client-mode mappings. It calls only `ListHosts`, `ListUsers`,
`ListTags`, and `ListSyncSettings`. It writes inventory to your Cartography graph,
not to Workshop.

## Authentication

Supply an existing Workshop API key through an environment variable. The connector
sends the key in the `Authorization` header, without a `Bearer` prefix, as documented
by North Pole Security. Do not put keys in command-line arguments or fixture files.

## Required permissions

| Permission | Purpose |
| --- | --- |
| `read:settings` | Call `ListSyncSettings` for configured client modes. |
| `read:hosts` | Call `ListHosts` for workstation details, primary users, and assigned tags. |
| `read:scim` | Call `ListUsers` for directory user details. |
| `read:tags` | Call `ListTags` for tags without a host or client-mode setting. |

All four RPCs are annotated `NO_SIDE_EFFECTS`. Use tenant-wide read permissions, not
`read:hosts:self`, which can produce a partial inventory. The expanded connector requires
all four reads; a key that previously had only `read:settings` must have these additional
read permissions before you rerun it. A denied read aborts without graph writes or cleanup;
the connector does not fall back to a partial sync or change the key's permissions.

No write, event, or policy-management permissions are required. This connector does not
create keys, request workstation commands, or change permissions.

## Configure Cartography

| Option | Purpose |
| --- | --- |
| `--workshop-api-url` | HTTPS tenant API origin, such as `https://example.workshop.cloud`. Paths, user information, queries, and fragments are rejected. Redirects are not followed. |
| `--workshop-apikey-env-var` | Name of the environment variable containing the existing API key. |
| `--workshop-tenant-id` | Stable, unique operator-defined scope for this tenant. |

All three options are required to enable ingestion. Keep each tenant scope bound to
exactly one Workshop tenant and key. The list response does not identify the tenant,
so the connector cannot independently verify this binding. Do not reuse scopes across
tenants or change them between runs. Run tenants separately with distinct scopes.

## Run Cartography

After you set `WORKSHOP_API_KEY` securely in your environment, run:

```bash
cartography --selected-modules workshop \
  --workshop-api-url https://example.workshop.cloud \
  --workshop-apikey-env-var WORKSHOP_API_KEY \
  --workshop-tenant-id example-tenant
```

The command is an operator example, not evidence of a live sync. Read the
[validation limits](limitations.md) before enabling this experimental connector.

## References

- [Workshop API authentication and HTTP transport](https://northpole.security/docs/workshop/api)
- [Vendor protobuf API](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.WorkshopService.ListSyncSettings)
