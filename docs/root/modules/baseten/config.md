# Baseten configuration

Cartography reads your Baseten organization through the read-only `GET` endpoints of the
[Baseten Management API](https://docs.baseten.co/reference/management-api/overview). It
needs one Baseten API key. The API is scoped to the key's organization, so you don't pass an
organization ID.

## Authentication

Baseten filters several Management API responses by the role of the key's owner, so use a
key that can see the whole organization:

- **Recommended:** a personal API key that belongs to an organization **Admin**. It's the
  only key type that can read the organization's members, every team, every team API key,
  and every member's personal API keys.
- A team API key with **Full access to all team models** reads only its own team's models,
  Chains, and secrets. Don't use one for an organization-wide inventory.
- An API key management key (`WORKSPACE_MANAGE_API_KEYS`) can only list teams, models, and
  API keys. Cartography can't sync the rest of the organization with it.

Baseten requires personal API keys to expire within 90 days, or sooner if your organization
sets a shorter limit, and revokes personal keys that go unused for 30 days. Rotate the key
before it expires. A daily sync keeps it from being revoked for inactivity.

To create the key, sign in to [app.baseten.co](https://app.baseten.co) as an organization
Admin, open **Organization settings** > [**API keys**](https://app.baseten.co/settings/api_keys),
choose **Create API key**, and select **Personal**. Store the key in an environment variable.

## Required permissions

Cartography calls these endpoints:

| Endpoint | Ingests | Who can read it |
| --- | --- | --- |
| `GET /v1/organizations/me` | `BasetenOrganization` | Any API key. |
| `GET /v1/teams` | `BasetenTeam` | Teams the key's owner can access. Organization Admins see every team. |
| `GET /v1/users` | `BasetenUser` | Not documented. Use an organization Admin's key. |
| `GET /v1/models`, `GET /v1/models/{model_id}/deployments` | `BasetenModel`, `BasetenDeployment` | Viewer role or higher in the model's team. |
| `GET /v1/chains` | `BasetenChain` | Viewer role or higher in the Chain's team. |
| `GET /v1/teams/{team_id}/secrets` | `BasetenSecret` (metadata only) | Viewer role or higher in the team. |
| `GET /v1/api_keys` | `BasetenApiKey` (metadata only) | Organization Admins see every key. Team Admins see their teams' keys. Other users see their own keys. |
| `GET /v1/teams/{team_id}/environment_groups` | `BasetenEnvironmentGroup` | Not documented. Use an organization Admin's key. |

If any endpoint fails, for example with `403 Forbidden`, the Baseten sync stops with an
error and leaves the previous sync's data in place.

## Configure Cartography

| Option | Description |
| --- | --- |
| `--baseten-api-key-env-var` | Name of the environment variable that holds the Baseten API key. |

## Run Cartography

```bash
export BASETEN_API_KEY='<api-key>'
cartography \
  --selected-modules baseten \
  --baseten-api-key-env-var BASETEN_API_KEY
```

## References

- [Baseten API keys](https://docs.baseten.co/organization/api-keys)
- [Baseten access control](https://docs.baseten.co/organization/access) and
  [teams](https://docs.baseten.co/organization/teams)
- [Management API OpenAPI specification](https://api.baseten.co/v1/spec)
