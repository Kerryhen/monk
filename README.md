# Monk — Listmonk Multi-Client API

A multitenancy middleware that adds per-client isolation on top of [Listmonk](https://listmonk.app/), an open-source email list management tool.

## Overview

Listmonk natively has no concept of per-client ownership — all lists and subscribers are global. Monk solves this by placing a FastAPI proxy in front of Listmonk that enforces strict client isolation:

- Each **client** owns a **default list** in Listmonk. Subscribers added by that client are enrolled in this default list first.
- Clients can create additional **sub-lists**, but only subscribers already in the client's default list can be enrolled in them.
- **Clients are fully isolated**: client X cannot see lists or subscribers belonging to client Y.
- Ownership metadata is stored in **PocketBase** (`monk_lists`, `monk_client_lists` collections); Listmonk remains the authoritative store for subscriber data and campaign delivery.

## Services

| Service | Description | Port |
|---------|-------------|------|
| `api` | FastAPI middleware/proxy (`services/api/`) | 8000 |
| `listmonk` | Email list management UI and API | 9000 |
| `pocketbase` | Ownership/multitenancy data store | 8090 |
| `listmonk_db` | PostgreSQL database for Listmonk | 5432 |

## Architecture

```
Client request (HTTP Basic Auth)
        │
        ▼
   FastAPI API (port 8000)
        │
        ├──► Listmonk API (port 9000)   — subscriber data, campaigns
        │
        └──► PocketBase (port 8090)     — client↔list ownership mapping
```

The `Interface` class (`services/api/app/interface.py`) is the single coordination point: every mutation is written to both Listmonk and PocketBase atomically.

### Auth

- **Inbound**: HTTP Basic Auth validated against `LISTMONK_USER` / `LISTMONK_TOKEN` env vars.
- **Outbound to PocketBase**: bot account (`POCKETBASE_BOT_EMAIL` / `POCKETBASE_BOT_PASSWORD`), authenticated as admin.

## API Endpoints

All routes are under `/list` and require a `?client=<client_id>` query parameter.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/list/` | Create a new list for a client |
| `DELETE` | `/list/` | Delete one or more lists by ID or query |
| `PATCH` | `/list/{list_id}` | Update a list's metadata |

## Getting Started

### Prerequisites

- Docker & Docker Compose
- [Doppler CLI](https://docs.doppler.com/docs/install-cli) (secrets management)

### Run all services

```bash
doppler run -- docker compose up
```

With live-reload for the API service:

```bash
doppler run -- docker compose up --build
```

## Development (API service)

All commands run from `services/api/` using [PDM](https://pdm-project.org/) and [taskipy](https://github.com/taskipy/taskipy):

```bash
cd services/api
```

| Task | Command |
|------|---------|
| Dev server | `doppler run -- pdm run task run` |
| Tests | `doppler run -- pdm run task test` |
| Lint | `pdm run task lint` |
| Format | `pdm run task format` |

Run a single test:

```bash
doppler run -- pdm run pytest tests/test_lists.py::test_create_list -s -x -vv
```

> Tests are **integration tests** that hit live Listmonk and PocketBase instances. Doppler-injected credentials are required.

## Environment Variables

All secrets are managed via Doppler. Key variables:

| Variable | Description |
|----------|-------------|
| `LISTMONK_USER` | API username for Listmonk |
| `LISTMONK_TOKEN` | API token for Listmonk |
| `LISTMONK_API_URL` | Listmonk base URL |
| `POCKETBASE_BOT_EMAIL` | PocketBase bot account email |
| `POCKETBASE_BOT_PASSWORD` | PocketBase bot account password |
| `POCKETBASE_API_URL` | PocketBase base URL |

## PocketBase Schema

### `monk_lists`

One record per Listmonk list.

| Field | Type | Notes |
|-------|------|-------|
| `id` | text (numeric) | mirrors Listmonk list ID |
| `created` | autodate | set on create |
| `updated` | autodate | set on create and update |

### `monk_client_lists`

Maps a client to its owned lists.

| Field | Type | Notes |
|-------|------|-------|
| `id` | text (alphanumeric) | PocketBase auto-generated |
| `client` | text | client identifier string |
| `lists` | relation[] → monk_lists | cascade delete |
| `created` | autodate | set on create |
| `updated` | autodate | set on create and update |

## Key Source Files

| File | Description |
|------|-------------|
| `services/api/app/interface.py` | `Interface` class — all business logic |
| `services/api/app/sessions.py` | Auth dependencies and HTTP clients |
| `services/api/app/schemas.py` | Pydantic request/response schemas |
| `services/api/app/routers/lists.py` | List CRUD endpoints |
| `services/pocketbase/pb_schema.json` | PocketBase collection schema |
