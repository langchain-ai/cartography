# Workshop configuration

This connector reads configured tag-to-client-mode mappings with `ListSyncSettings` only.
It writes the resulting inventory to your Cartography graph, not to Workshop.

## Authentication

Supply an existing Workshop API key through an environment variable. The connector
sends the key in the `Authorization` header, without a `Bearer` prefix, as documented
by North Pole Security. Do not put keys in command-line arguments or fixture files.

## Required permissions

| Permission | Purpose |
| --- | --- |
| `read:settings` | Call the side-effect-free `ListSyncSettings` RPC. |

No write, event, host, or policy-management permissions are required. Use a key limited
to read-only settings access. This connector does not create keys or change permissions.

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
