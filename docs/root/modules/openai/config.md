# OpenAI Configuration

## Authentication

Create a read-only Admin API key in the [OpenAI Platform API settings](https://platform.openai.com/settings/organization/admin-keys) and store it in an environment variable.

Find the organization ID, such as `org-xxxxxxxxxx`, in the [organization settings](https://platform.openai.com/settings/organization/general).

## Required Permissions

Use a read-only Admin API key.

Cartography also reads the organization and project data retention controls, such as zero data retention. If the key can't read them, Cartography logs a warning and leaves `data_retention` empty.

## Configure Cartography

Provide these options:

- `--openai-apikey-env-var`: Name of the environment variable containing the Admin API key.
- `--openai-org-id`: OpenAI organization ID.

## Run Cartography

```bash
export OPENAI_ADMIN_API_KEY='<admin-api-key>'
cartography \
  --selected-modules openai \
  --openai-apikey-env-var OPENAI_ADMIN_API_KEY \
  --openai-org-id '<organization-id>'
```
