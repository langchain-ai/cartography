# Fireworks AI configuration

Cartography reads a Fireworks AI account through the
[Fireworks AI REST API](https://docs.fireworks.ai/api-reference/introduction)
with an API key and the account ID.

## Authentication

Fireworks AI API keys belong to a user or a service account, and a key can do
whatever its owner's role allows. Use a dedicated service account so that audit
logs separate Cartography from people:

```bash
firectl user create --user-id cartography --service-account --role admin
firectl api-key create --service-account cartography
```

Find the account ID in the [Fireworks AI console](https://app.fireworks.ai) or
with `firectl account list`. Developer accounts derive the ID from the sign-up
email address. Enterprise accounts can choose their own.

## Required permissions

Any role can read the account, its users and service accounts, models,
deployments, datasets, and policy settings.

| Resource | Endpoint | Role that can read it |
| --- | --- | --- |
| Account | `GET /v1/accounts/{account_id}` | Any role |
| Policy settings | `GET /v1/accounts/{account_id}/policySettings` | Any role |
| Users and service accounts | `GET /v1/accounts/{account_id}/users` | Any role |
| Models | `GET /v1/accounts/{account_id}/models` | Any role |
| Deployments | `GET /v1/accounts/{account_id}/deployments` | Any role |
| Datasets | `GET /v1/accounts/{account_id}/datasets` | Any role |

## Optional permissions

These resources need more than the lowest role. When the API key can't read one,
Cartography logs a warning, skips it, and keeps what an earlier sync stored.

| Resource | Endpoint | Requirement |
| --- | --- | --- |
| API keys for every user | `GET /v1/accounts/{account_id}/users/-/apiKeys` | The key's owner must have the `admin` role. |
| Secrets | `GET /v1/accounts/{account_id}/secrets` | The Fireworks AI documentation doesn't say which role is needed. |
| SSO identity providers | `GET /v1/accounts/{account_id}/identityProviders` | Custom SSO needs an Enterprise account. The Fireworks AI documentation doesn't say which role can read it. |

Fireworks AI API keys have no read-only scope, so an `admin` key can also
change the account. Store it as you would any other admin credential.

## Configure Cartography

| Option | Description |
| --- | --- |
| `--fireworks-apikey-env-var` | Name of the environment variable that holds the Fireworks AI API key. |
| `--fireworks-account-id` | Fireworks AI account ID to sync, such as `my-account`. |

Cartography skips the module unless both options are set.

## Run Cartography

```bash
export FIREWORKS_API_KEY='<api-key>'
cartography \
  --selected-modules fireworks \
  --fireworks-apikey-env-var FIREWORKS_API_KEY \
  --fireworks-account-id '<account-id>'
```

## References

- [Managing users and roles](https://docs.fireworks.ai/accounts/users)
- [Service accounts](https://docs.fireworks.ai/accounts/service-accounts)
- [List API keys](https://docs.fireworks.ai/api-reference/list-api-keys)
- [Get policy settings](https://docs.fireworks.ai/api-reference/get-policy-settings)
