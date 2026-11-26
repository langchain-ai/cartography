# Workshop queries

Run these read-only Cypher queries in the same Neo4j database used by the sync.
Replace `example-tenant` with your `--workshop-tenant-id` value.

## Workstations and primary users

```cypher
MATCH (h:WorkshopHost {tenant_id: 'example-tenant'})
OPTIONAL MATCH (h)-[:PRIMARY_USER]->(u:WorkshopUser)
RETURN h.hostname AS hostname,
       h.uuid AS uuid,
       h.primary_user AS reported_primary_user,
       u.username AS directory_username,
       u.department_name AS department,
       h.os_version AS os_version,
       h.last_sync AS last_sync
ORDER BY hostname;
```

A null directory username can mean that the reported primary user is absent from the
directory inventory or that more than one directory record has that exact username.

## Workstation tags and their configured modes

```cypher
MATCH (h:WorkshopHost {tenant_id: 'example-tenant'})
OPTIONAL MATCH (h)-[:HAS_TAG]->(t:WorkshopTag)
OPTIONAL MATCH (t)-[:CONFIGURED_CLIENT_MODE]->(m:WorkshopClientMode)
RETURN h.hostname AS hostname,
       t.tag AS tag,
       m.name AS tag_configured_client_mode
ORDER BY hostname, tag;
```

This query shows tag configuration, not the workstation's effective mode. A tag without
a settings record has no configured-mode edge. The graph does not synthesize implicit
global or host-specific membership when it is absent from the host's returned tags.

## Visualize inventory relationships

```cypher
MATCH p = (:WorkshopHost {tenant_id: 'example-tenant'})-[:HAS_TAG|PRIMARY_USER]->()
RETURN p
LIMIT 100;
```
