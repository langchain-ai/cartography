# Workshop scope and validation limits

## Inventory and configured values, not effective policy

The graph contains a `WorkshopTenant` and tenant-scoped `WorkshopHost`, `WorkshopUser`,
`WorkshopTag`, and `WorkshopClientMode` nodes. IDs use unambiguous JSON tuples to avoid
cross-tenant collisions. The connector retains selected fields only, not raw responses.

- Workstations: opaque UUID, hostname, serial number, model, OS version/build, Santa
  version, last communication timestamp, primary username, and reported primary-user
  group names from `ListHosts`. These are inventory observations, not proof of ownership,
  current login sessions, complete local accounts, or enforcement status.
- Users: directory ID, username, manager email, department, cost center, and directory
  type from `ListUsers`. The public `User` message has no display-name or separate email
  field; the connector does not invent either from a username. Directory data can be
  empty or stale when the tenant does not synchronize users.
- Host-to-tag `HAS_TAG` edges use only the host's returned `tags` list. The connector
  does not synthesize implicit tags, resolve ordering, or infer membership from groups.
- Host-to-user `PRIMARY_USER` edges require an exact match with exactly one directory
  username in the same tenant. An unmatched or ambiguous primary username remains on
  the host without a guessed directory link. No cross-provider user matching is performed.
- Tags are the union of `ListTags`, host memberships, and `ListSyncSettings`. A tag has
  a `CONFIGURED_CLIENT_MODE` edge only when settings return that tag. A missing or zero
  mode in a returned settings record remains `UNKNOWN_CLIENT_MODE`, not monitor mode.
  A catalog-only or membership-only tag has no configured-mode edge.

`global` and host-specific settings remain tag configuration keys. No effective host
policy, tag precedence evaluation, compliance verdicts, raw events, profile pictures,
user group-membership graph, or commands are collected or inferred. API keys and response
bodies are not logged or stored in the graph. Inventory contains personal and device
identifiers; restrict access to your local graph and do not commit real exports as fixtures.

## Paging and failure safety

The public protobuf definitions declare numbered `page_size` and `page` request fields.
Vendor examples start at `page: 1`. The connector requests unfiltered pages of 100 records:

- `ListSyncSettingsResponse` has only repeated settings, with no pagination metadata.
  Continue past short pages to an empty terminal page.
- `ListHostsResponse`, `ListUsersResponse`, and `ListTagsResponse` provide an optional
  `more` flag. Explicit `false` ends the read; `true` requires another nonempty page.
  If omitted, continue past short pages to an empty terminal page.
- `ListHostsResponse.count` is exact up to 10,000, and means "more than 10,000" above
  that threshold. When present, validate this count and reject changes across pages.
  It is not an exact total for larger inventories. Protobuf int64 strings are accepted.

An empty JSON object represents omitted-empty repeated fields. Conflicting aliases,
unexpected response-envelope fields, invalid records, duplicate IDs, repeated pages,
empty pages claiming more results, inconsistent counts, and the 10,000-page safety bound
abort ingestion. `Host.tags_truncated: true` also aborts: Workshop explicitly signals
that some group-derived tags were dropped, so the returned set is incomplete.

All four reads and all selected field transformations complete before any graph writes
or cleanup. A denied permission, transport failure, or detectable incomplete response
preserves prior graph contents. Successful cleanup removes stale nodes and tag, user,
and configured-mode relationships only within the configured tenant. A complete empty
read removes that tenant's resources; the tenant scope node remains.

These APIs offer no snapshot identifier. They cannot prove that records were not silently
skipped during concurrent edits, or distinguish a falsely empty response or restricted
visibility from a genuinely empty inventory. Use tenant-wide credentials and a quiet
configuration window. Graph loading and cleanup use normal Cartography transactions,
not one atomic whole-sync transaction; database write failures require rerunning the sync.

## Validation performed and remaining limits

Development uses deterministic synthetic payloads and disposable local Neo4j only.
No Workshop credentials, private identifiers in fixtures, live API access by the developer
agent, raw events, policy changes, upstream submission, merge, or deployment are part of
this change. Operator-provided output from the initial settings-only sync is not live
validation of the expanded inventory endpoints.

Public documentation establishes the read permissions, `NO_SIDE_EFFECTS` annotations,
raw-key authorization, request and response schemas, and enum definitions. Live permission
enforcement, deployed JSON serialization, actual terminal behavior, server-side caps,
consistency during concurrent updates, and production scale remain unverified. Keep the
fork PR in draft; synthetic tests do not satisfy upstream real-provider evidence requirements.

## Vendor definitions

- [Service and read permissions](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.WorkshopService)
- [Host fields](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.Host)
- [Host list response](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.ListHostsResponse)
- [User fields](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.User)
- [User list response](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.ListUsersResponse)
- [Tag list response](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.ListTagsResponse)
- [Settings list response](https://buf.build/northpolesec/workshop-api/docs/main%3Aworkshop.v1#workshop.v1.ListSyncSettingsResponse)
