import logging


def configure_logging() -> None:
    """Configure application logging.

    Uses stdlib logging with structured fields via `extra=` on every call site.
    LogRecord attributes populated via `extra=` are ready to be forwarded to
    OpenTelemetry as span attributes — add `LoggingInstrumentor().instrument()`
    here when OTel is introduced, with no changes needed at call sites.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
    )
