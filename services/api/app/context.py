from contextvars import ContextVar
from typing import Optional

_wide_event_var: ContextVar[Optional[dict]] = ContextVar('wide_event', default=None)


def set_wide_event(event: dict) -> None:
    _wide_event_var.set(event)


def enrich_wide_event(data: dict) -> None:
    """Merge data into the current request's wide event.

    No-op when called outside of a request context (e.g. direct Interface calls in tests).
    ContextVar is copied to threadpool threads via asyncio.run_in_executor, so sync
    FastAPI handlers can safely call this.  Mutations to the shared dict are visible
    across the copy boundary because both contexts hold a reference to the same object.
    """
    event = _wide_event_var.get()
    if event is not None:
        event.update(data)
