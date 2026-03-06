# Observability

The API uses Python's stdlib `logging` module with structured fields. The design is intentionally minimal now and ready for OpenTelemetry later — no call sites need to change when OTel is introduced.

## Logging setup

All logging configuration lives in one place: `app/logging_config.py`. It is called once at app startup in `app/main.py`.

```python
# app/logging_config.py
def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
    )
    # Future: LoggingInstrumentor().instrument() goes here
```

Never call `logging.basicConfig()` anywhere else in the codebase.

## Structured fields

Every log call uses `extra=` to attach structured key-value pairs to the `LogRecord`. This makes logs parseable today and gives OpenTelemetry span attributes for free tomorrow.

```python
logger.info('create_list.ok', extra={'client': client, 'list_id': list_id, 'list_name': name})
logger.error('create_campaign.forbidden', extra={'client': client_id, 'list_id': list_id})
```

### Reserved keys

Python's `LogRecord` has built-in attributes that **cannot** be used as `extra=` keys — they will raise `KeyError` at runtime:

`name`, `msg`, `args`, `levelname`, `levelno`, `pathname`, `filename`, `module`, `lineno`, `funcName`, `created`, `msecs`, `thread`, `threadName`, `process`, `processName`, `message`, `asctime`

Use prefixed or descriptive alternatives: `list_name`, `campaign_name`, `file` instead of `name`, `name`, `filename`.

## What is logged

### `app.interface`

| Event | Level | Fields |
|-------|-------|--------|
| `create_list.ok` | INFO | `client`, `list_id`, `list_name` |
| `create_list.unreachable` | ERROR | `client`, `error` |
| `delete_list.ok` | INFO | `client`, `ids` |
| `update_list.ok` | INFO | `client`, `list_id` |
| `create_campaign.ok` | INFO | `client`, `campaign_id`, `campaign_name` |
| `create_campaign.forbidden` | ERROR | `client`, `list_id` |
| `create_campaign.unreachable` | ERROR | `client`, `error` |
| `get_campaigns.ok` | INFO | `client`, `count` |
| `update_campaign.ok` | INFO | `client`, `campaign_id` |
| `delete_campaign.ok` | INFO | `client`, `campaign_id` |
| `set_campaign_status.ok` | INFO | `client`, `campaign_id`, `status` |
| `import_subscribers.ok` | INFO | `client`, `default_list`, `file` |
| `import_subscribers.no_default_list` | ERROR | `client` |
| `import_subscribers.unreachable` | ERROR | `client`, `error` |

### `app.sessions`

| Event | Level | Fields |
|-------|-------|--------|
| `auth.invalid_credentials` | WARNING | `username` |
| `pocketbase.auth_failed` | ERROR | `error` |
| `pocketbase.token_invalid` | ERROR | — |

### `app.handlers.fake`

| Event | Level | Fields |
|-------|-------|--------|
| `fake_handler.send` | INFO | `campaign`, `subject`, `recipients` |

## Adding OpenTelemetry (future)

When ready, install the SDK and update only `app/logging_config.py`:

```bash
pdm add opentelemetry-sdk opentelemetry-instrumentation-logging opentelemetry-instrumentation-fastapi
```

```python
# app/logging_config.py
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider

def configure_logging() -> None:
    LoggingInstrumentor().instrument()   # bridges stdlib logging → OTel
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
    )
```

All `extra=` fields on existing log calls become OTel span attributes automatically. No other files need to change.
