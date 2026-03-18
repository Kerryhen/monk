# Observability

The API uses Python's stdlib `logging` module with **wide events** (canonical log lines): one structured JSON event emitted per request at the HTTP boundary, enriched with business context from the handler.

## Architecture

```
Request
  │
  ├─ WideEventMiddleware (app/middleware.py)
  │    • generates request_id
  │    • initialises wide_event dict with HTTP + env context
  │    • stores dict in ContextVar (propagates to threadpool threads)
  │    • emits single JSON log in finally block (INFO / ERROR)
  │
  ├─ Route handler
  │
  └─ Interface method (app/interface.py)
       • calls enrich_wide_event() with operation + business context
       • no logger import needed
```

## Logging setup

`app/logging_config.py` configures a single JSON handler on `logging.root`, called once at startup in `app/main.py`.

```python
# app/logging_config.py
def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.root.setLevel(logging.INFO)
    logging.root.handlers = [handler]
    # Future: LoggingInstrumentor().instrument() goes here
```

Never call `configure_logging()` or `logging.basicConfig()` anywhere else in the codebase.

## Enriching the wide event

Business logic enriches the request-scoped wide event dict via `enrich_wide_event()`:

```python
from app.context import enrich_wide_event

enrich_wide_event({'operation': 'create_list', 'client_id': client, 'list': {'id': list_id, 'name': name}})
enrich_wide_event({'error': {'type': 'forbidden', 'list_id': list_id}})
```

`enrich_wide_event` is a no-op when called outside of a request context (e.g. direct Interface calls in tests).

## Wide event schema

Every emitted event includes:

| Field | Source | Example |
|-------|--------|---------|
| `timestamp` | middleware | `2024-09-08T06:14:05.680123` |
| `level` | middleware | `info` / `error` |
| `logger` | middleware | `app.middleware` |
| `event` | middleware | `request` |
| `request_id` | middleware | `x-request-id` header or UUID |
| `method` | middleware | `POST` |
| `path` | middleware | `/v1/list` |
| `status_code` | middleware | `201` |
| `outcome` | middleware | `success` / `error` |
| `duration_ms` | middleware | `245.3` |
| `service` | env | `monk-api` |
| `version` | package metadata | `0.1.1` |
| `environment` | `ENVIRONMENT` env var | `PRD` |
| `commit_sha` | `COMMIT_SHA` env var | `abc1234` |
| `operation` | interface | `create_list` |
| `client_id` | interface | `acme-corp` |
| business fields | interface | operation-specific (see below) |

## Business context by operation

### Lists

| Operation | Fields added |
|-----------|-------------|
| `get_lists` | `client_id`, `count` |
| `create_list` | `client_id`, `list.id`, `list.name` |
| `update_list` | `client_id`, `list_id` |
| `delete_list` | `client_id`, `list_ids` |

### Campaigns

| Operation | Fields added |
|-----------|-------------|
| `get_campaigns` | `client_id`, `count` |
| `create_campaign` | `client_id`, `campaign.id`, `campaign.name` |
| `update_campaign` | `client_id`, `campaign_id` |
| `delete_campaign` | `client_id`, `campaign_id` |
| `set_campaign_status` | `client_id`, `campaign_id`, `status` |

### Subscribers

| Operation | Fields added |
|-----------|-------------|
| `import_subscribers` | `client_id`, `target_list`, `file` |
| `import_subscribers_json` | `client_id`, `target_list`, `count` |
| `delete_subscriber` | `email` (ok), or `error.type` + `email` |

Auto-create also adds `auto_created_client: true`.

### Auth

| Outcome | Fields added |
|---------|-------------|
| Invalid credentials | `auth.outcome`, `auth.username` |

### Error shape

```json
{
  "error": {
    "type": "forbidden | service_unavailable | list_not_found | ...",
    "message": "...",   // for service_unavailable
    "list_id": 99       // where applicable
  }
}
```

## Log levels

- **INFO** — all requests with `status_code < 400`
- **ERROR** — all requests with `status_code >= 400`

No other levels are used.

## Example output

```json
{
  "timestamp": "2024-09-08T06:14:05.680123",
  "level": "info",
  "logger": "app.middleware",
  "event": "request",
  "request_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "method": "POST",
  "path": "/v1/list",
  "status_code": 201,
  "outcome": "success",
  "duration_ms": 245.3,
  "service": "monk-api",
  "version": "0.1.1",
  "environment": "PRD",
  "commit_sha": "abc1234",
  "operation": "create_list",
  "client_id": "acme-corp",
  "list": {"id": 42, "name": "Newsletter"}
}
```

## Reserved LogRecord keys

Python's `LogRecord` has built-in attributes that cannot be used as `extra=` keys — they will raise `KeyError` at runtime. These are filtered by `_JSONFormatter` in `logging_config.py`. If you add direct `logger.*` calls (e.g. for startup-time errors in `sessions.py`), avoid these keys in `extra=`:

`name`, `msg`, `args`, `levelname`, `levelno`, `pathname`, `filename`, `module`, `lineno`, `funcName`, `created`, `msecs`, `thread`, `threadName`, `process`, `processName`, `message`, `asctime`

## Adding OpenTelemetry (future)

When ready, install the SDK and update only `app/logging_config.py`:

```bash
pdm add opentelemetry-sdk opentelemetry-instrumentation-logging opentelemetry-instrumentation-fastapi
```

```python
# app/logging_config.py
from opentelemetry.instrumentation.logging import LoggingInstrumentor

def configure_logging() -> None:
    LoggingInstrumentor().instrument()   # bridges stdlib logging → OTel
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.root.setLevel(logging.INFO)
    logging.root.handlers = [handler]
```

All `extra=` fields on existing log calls become OTel span attributes automatically. No other files need to change.
