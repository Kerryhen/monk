# PocketBase Service

PocketBase stores the client→list ownership mappings that the API service uses to enforce multitenancy.

The schema is defined in `pb_schema.json`.

> **Note:** The schema is provisional and will change as new features are added.

## Collections

### `monk_lists`

One record per Listmonk list.

| Field | Type | Notes |
|-------|------|-------|
| id | text (numeric pattern) | mirrors Listmonk list ID |
| created | autodate | set on create |
| updated | autodate | set on create and update |

### `monk_client_lists`

Maps a client to its owned lists.

| Field | Type | Notes |
|-------|------|-------|
| id | text (alphanumeric) | PocketBase auto-generated |
| client | text | client identifier string |
| lists | relation[] → monk_lists | cascade delete |
| created | autodate | set on create |
| updated | autodate | set on create and update |
