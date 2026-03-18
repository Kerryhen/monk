import json
import logging

# Built-in LogRecord attributes that must not be re-emitted as extra fields.
_RESERVED = frozenset({
    'args',
    'asctime',
    'created',
    'exc_info',
    'exc_text',
    'filename',
    'funcName',
    'levelname',
    'levelno',
    'lineno',
    'message',
    'module',
    'msecs',
    'msg',
    'name',
    'pathname',
    'process',
    'processName',
    'relativeCreated',
    'stack_info',
    'taskName',
    'thread',
    'threadName',
})


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        log: dict = {
            'timestamp': self.formatTime(record, '%Y-%m-%dT%H:%M:%S.%f'),
            'level': record.levelname.lower(),
            'logger': record.name,
            'event': record.message,
        }
        if record.exc_info:
            log['exception'] = self.formatException(record.exc_info)
        log.update({k: v for k, v in record.__dict__.items() if k not in _RESERVED and not k.startswith('_')})
        return json.dumps(log, default=str)


def configure_logging() -> None:
    """Configure application logging with structured JSON output.

    Uses stdlib logging with structured fields via `extra=` on every call site.
    LogRecord attributes populated via `extra=` are ready to be forwarded to
    OpenTelemetry as span attributes — add `LoggingInstrumentor().instrument()`
    here when OTel is introduced, with no changes needed at call sites.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.root.setLevel(logging.INFO)
    logging.root.handlers = [handler]
