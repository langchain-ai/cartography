# Stripe configuration

Cartography reads your Stripe account, webhook endpoints, event destinations,
installed Stripe Apps, and optionally your Connect connected accounts. It needs a
Stripe API key that can read them.

Cartography reads configuration and security metadata only. It doesn't call
endpoints for customers, payment methods, charges, payouts, balances, persons,
or bank accounts, and it drops legal-entity, terms-of-service acceptance, and
`metadata` fields from the objects that it reads.

## Authentication

Use a [restricted API key](https://docs.stripe.com/keys/restricted-api-keys)
that only has read permissions. Don't use a secret key (`sk_...`), because it
can do anything in your account.

1. In the Stripe Dashboard, go to [API keys](https://dashboard.stripe.com/apikeys)
   and click **Create restricted key**.
1. Name the key, for example `cartography-read-only`.
1. Set every permission to **None**, then grant the permissions in
   [Required permissions](#required-permissions) and the
   [optional permissions](#optional-permissions) for the resources that you
   want to sync.
1. Create the key and store it in your secrets manager.
1. Optional: attach an [access policy](https://docs.stripe.com/keys#access-policies)
   that only allows requests from the network where Cartography runs.

Create the key in live mode to sync your production account. A sandbox key
syncs the sandbox instead.

## Required permissions

| Resource | Permission | Endpoint |
| --- | --- | --- |
| Accounts | Read | `GET /v1/account`, and `GET /v1/accounts` with `--stripe-sync-connected-accounts` |

Without it, the sync fails.

## Optional permissions

Cartography skips a resource and keeps its existing nodes when Stripe refuses
the request with `403 Forbidden`.

| Resource | Permission | Endpoint | Nodes |
| --- | --- | --- | --- |
| Webhook Endpoints | Read | `GET /v1/webhook_endpoints`, `GET /v2/core/event_destinations` | `StripeWebhookEndpoint`, `StripeEventDestination` |
| Stripe Apps installs | Read | `GET /v1/apps/installs` | `StripeAppInstall` |

Stripe doesn't document which restricted key permission covers
`GET /v1/apps/installs`. If the sync logs that it can't read app installs, check
the key's [request logs](https://docs.stripe.com/keys#view-request-logs) for the
permission that Stripe asks for.

## Configure Cartography

| Option | Description |
| --- | --- |
| `--stripe-api-key-env-var` | Name of the environment variable that holds the Stripe API key. Required to run the module. |
| `--stripe-sync-connected-accounts` | Also sync the accounts connected to a Connect platform. Off by default, because a platform can have many connected accounts. |

Cartography pins every request to Stripe API version `2026-11-18.endive`, so
your account's default API version doesn't change what it reads.

## Run Cartography

```bash
export STRIPE_API_KEY=rk_live_...
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules stripe \
  --stripe-api-key-env-var STRIPE_API_KEY
```

To link Amazon EventBridge and Azure Event Grid destinations to your AWS
accounts and Azure subscriptions, sync the `aws` and `azure` modules before
`stripe`.

## Advanced configuration

Cartography syncs one Stripe account per run: the account that owns the API key.
To sync several accounts, run the module once for each account's key.

Organization API keys (`sk_org_...`) need a `Stripe-Context` header for each
account, which Cartography doesn't send yet.

## References

The Stripe API doesn't expose these security settings, so Cartography can't
read them:

- Team members, their roles, and pending invites.
- Single sign-on, SCIM, and two-step authentication enforcement.
- The API key inventory, each key's permissions, and access policies.
- Radar rules and risk settings.
- Security history and data retention settings.

See the [Stripe API reference](https://docs.stripe.com/api) for the endpoints
that Cartography reads.
