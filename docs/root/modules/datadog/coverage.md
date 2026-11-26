# Datadog coverage and sync safety

The Datadog module covers access governance: who has access to the
organization, which roles they hold, and what those roles permit. This page
lists what the module reads, how it protects existing graph data, and what it
doesn't cover.

## Collected data

| Node or relationship | Fields |
| --- | --- |
| `DatadogOrganization` | ID, name, public ID, API base URL |
| `DatadogUser` | ID, email, status, disabled, created and modified times |
| `DatadogServiceAccount` | ID, name, email, status, disabled, created and modified times |
| `DatadogRole` | ID, name, created and modified times, user count, permission names, inherited managed roles |
| `HAS_ROLE` | Role memberships of users and service accounts |

Transforms copy an explicit list of fields, so other attributes in Datadog's
responses never reach the graph. In particular, Cartography doesn't collect:

- Profile and sign-in details: a person's name, handle, title, icon,
  verification state, MFA state, allowed login methods, and last sign-in.
- Credentials: API keys, application keys, personal access tokens, and
  service access tokens, including their metadata.
- Logs or any other telemetry.

## Sync safety

Cartography deletes stale Datadog nodes only after it reads a complete listing
of that node type:

- **Complete listings only**: Each list endpoint is read 100 items per page.
  Every page must report the same total in `meta.page`, no item may appear on
  two pages, and the item count must match the total. Otherwise, Cartography
  retries the whole listing up to three times and then raises
  `DatadogIncompleteListError` before it loads or cleans up anything of that
  type.
- **Denied and failed reads stop cleanup**: `401` and `403` responses, other
  HTTP errors, exhausted `429` or `5xx` retries, and timeouts propagate, so
  the cleanup for that type and every later type never runs.
- **Empty listings fail**: The credential's own account and the managed roles
  always exist, so an empty user or role listing raises instead of deleting
  every user or role.
- **Organization scope**: Cleanup only touches nodes attached to the
  organization that the credential belongs to.
- **Read-only client**: The HTTP session refuses every method except `GET`.

## Coverage gaps

The module doesn't read these Datadog access controls:

| Resource | Endpoint | Why it matters |
| --- | --- | --- |
| Teams and team memberships | `GET /api/v2/team` (`teams_read`) | Teams grant team-scoped roles and own resources. |
| SAML role mappings | `GET /api/v2/authn_mappings` (`user_access_read`) | Mappings assign roles from identity provider attributes. The resulting role memberships are still synced. |
| Organization login settings | `GET /api/v1/org/{public_id}` | SAML strict mode and default login methods. The API reference doesn't list the required permission. |
| Restriction policies | `GET /api/v2/restriction_policy/{resource_id}` | Per-resource access grants on dashboards, monitors, and other objects. There's no list endpoint, so each resource must be read separately. |

API limits:

- **Managed roles**: The API doesn't flag managed roles, and role names aren't
  unique, so `DatadogRole` doesn't record whether a role is built in.
- **Other organizations**: A user's memberships in other organizations aren't
  synced. Run Cartography with a credential from each organization.
