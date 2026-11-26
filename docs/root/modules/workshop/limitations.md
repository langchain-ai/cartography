# Workshop scope and validation limits

## Configured values, not effective policy

The graph contains only `WorkshopTenant`, tenant-scoped `WorkshopTag`, and
tenant-scoped `WorkshopClientMode` nodes. A tag has a `CONFIGURED_CLIENT_MODE` edge
to its configured mode. The connector keeps the vendor's `UNKNOWN_CLIENT_MODE`
value when the field is omitted or zero; it does not interpret that as monitor mode.
Tenant and resource IDs use unambiguous JSON tuples to avoid cross-tenant collisions.

Literal tags, including `global` and host-specific tags, remain opaque configuration
keys. No host nodes, tag membership, tag precedence, rule evaluation, effective host
policy, enforcement status, compliance verdicts, or raw events are collected or inferred.
Only tag and client-mode fields are retained from the settings response. API keys,
other settings, and response bodies are not logged or stored in the graph.

## Paging and failure safety

The public vendor protobuf definitions declare:

- `ListSyncSettingsRequest`: optional `uint32 page_size`, `uint32 page`, and `string filter`.
- `ListSyncSettingsResponse`: repeated `SyncSettings sync_settings`, with no total,
  next-page token, cursor, or snapshot identifier.
- The vendor RPC example starts at `page: 1`.

The connector requests unfiltered numbered pages with `pageSize: 100`. It continues
past short, nonempty pages, allowing for a server-side page-size cap, and requires an
empty terminal page. An empty JSON object is also an empty page under protobuf JSON's
omitted-repeated-field convention. Both protobuf snake-case and JSON lower-camel-case
field names are accepted. Conflicting aliases and unexpected response-envelope fields
are rejected rather than silently ignoring possible new pagination metadata.

HTTP failures, redirects, malformed pages, invalid modes, duplicate tags, repeated
pages, and exhaustion of the 10,000-page safety bound abort ingestion before any graph
writes or cleanup. Records are validated in full before loading. A complete empty
read removes prior tags and modes only in the configured tenant. After successful
loading, schema-based cleanup removes obsolete tag-to-mode edges and resources only
in that tenant; tenant scope nodes themselves remain.

The schema verifies the wire fields, not the deployed server's paging implementation.
It does not document snapshot isolation or provide a way to prove that records were
not silently skipped during concurrent edits. Use a quiet configuration window.
Undetectable provider-side truncation or an incorrectly empty provider response cannot
be distinguished from a complete read by this API. Graph loading and cleanup use
Cartography's normal transactions, not one atomic whole-sync transaction; a database
write failure must be rerun and is distinct from a provider read failure.

## Validation performed and remaining limits

Development uses deterministic synthetic payloads and a disposable local Neo4j only.
No Workshop credentials, private identifiers, live API access, raw events, policy
changes, upstream submission, merge, or deployment are part of this change.

Public documentation establishes `read:settings`, the `NO_SIDE_EFFECTS` RPC annotation,
raw-key authorization, numbered request fields, response shape, and client-mode enums.
Live permission enforcement, deployed JSON serialization, actual page numbering and
terminal behavior, server-side caps, consistency during concurrent updates, and
production scale remain unverified. Mocked pagination and local graph tests do not
prove live compatibility. Keep the fork PR in draft; it does not satisfy the project's
real-provider evidence requirement for upstream review.

## Vendor definitions

- [List request](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.ListSyncSettingsRequest)
- [List response](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.ListSyncSettingsResponse)
- [Tag settings](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.SyncSettings)
- [Client-mode enum](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.ClientMode)
