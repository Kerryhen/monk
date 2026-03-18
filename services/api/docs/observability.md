# Observability

The API uses Python's stdlib `logging` module with **wide events** (canonical log lines): one structured JSON event emitted per request at the HTTP boundary, enriched with business context from the handler.

## Architecture

```
Request
  │
  ├─ OpenTelemetryMiddleware (when OTEL_EXPORTER_OTLP_ENDPOINT is set)
  │    • outermost — starts root span; exports via OTLP/gRPC
  │
  ├─ WideEventMiddleware (app/middleware.py)
  │    • generates request_id
  │    • initialises wide_event dict with HTTP + env context
  │    • stores dict in ContextVar (propagates to threadpool threads)
  │    • emits single JSON log in finally block (INFO / ERROR)
  │    • when OTel is active: otelTraceID/otelSpanID injected automatically
  │      by LoggingInstrumentor into the log record
  │
  ├─ Route handler
  │
  └─ Interface method (app/interface.py)
       • calls enrich_wide_event() with operation + business context
       • no logger import needed
       • outbound requests.Session calls produce child spans automatically
         via RequestsInstrumentor
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

## OpenTelemetry

OTel is opt-in: set `OTEL_EXPORTER_OTLP_ENDPOINT` in Doppler to activate it.
When the env var is absent the app runs without tracing and the wide event schema is unchanged.

```bash
# Doppler — enable tracing (gRPC endpoint)
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

`app/telemetry.py` is called from `main.py` after middleware registration:

```python
configure_telemetry(app)   # no-op when env var absent
```

### What gets instrumented

| Component | Instrumentation | Result |
|-----------|----------------|--------|
| FastAPI | `FastAPIInstrumentor` | root span per HTTP request |
| `requests` library | `RequestsInstrumentor` | child span per Listmonk call |
| stdlib `logging` | `LoggingInstrumentor` | `otelTraceID`/`otelSpanID` injected into every log record |

### Trace correlation in logs

When OTel is active, the wide event automatically includes trace context:

```json
{
  "otelTraceID": "4bf92f3577b34da6a3ce929d0e0e4736",
  "otelSpanID": "00f067aa0ba902b7",
  "otelServiceName": "monk-api",
  "otelTraceSampled": true
}
```

No call-site changes are needed — `_JSONFormatter` picks up these fields from the log record the same way it picks up any other `extra=` field.
