# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment / Secrets

All env vars are managed via **Doppler**. Prefix any command that needs environment variables:

```
doppler run -- <command>
```

Examples: `doppler run -- docker compose up`, `doppler run -- docker compose up --build`.

## Services

| Service | Path | Description |
|---------|------|-------------|
| `api` | `services/api/` | FastAPI multitenancy middleware — see its own `CLAUDE.md` for full details |
| `listmonk` | `services/listmonk/` | Email list management tool |
| `pocketbase` | `services/pocketbase/` | Ownership/multitenancy data store |

The root `docker-compose.yml` orchestrates all services together.

## API Service Quick Reference

All API commands run from `services/api/` via `pdm run task <name>`:

| Task | Command |
|------|---------|
| Dev server | `doppler run -- pdm run task run` |
| Test | `doppler run -- pdm run task test` |
| Lint | `pdm run task lint` |
| Format | `pdm run task format` |

Single test: `doppler run -- pdm run pytest tests/test_lists.py::test_create_list -s -x -vv`

## Architecture Overview

The **API service** is a proxy/middleware between two backends:

- **Listmonk** — stores subscribers and handles email delivery. Accessed via HTTP Basic Auth.
- **PocketBase** — stores client→list ownership mappings (`monk_client_lists`, `monk_lists`). All mutations to Listmonk are mirrored here.

The `Interface` class (`services/api/app/routers/__init__.py`) is the single point of coordination: every operation writes to both Listmonk and PocketBase atomically. Inbound auth uses HTTP Basic Auth validated against `LISTMONK_USER`/`LISTMONK_TOKEN` env vars.

Tests are **integration tests** that hit live Listmonk and PocketBase — Doppler-injected credentials are required.
