# Messenger Handlers

The API acts as a custom [Listmonk messenger](https://listmonk.app/docs/messengers/) — a gateway that receives campaign messages from Listmonk and forwards them to a pluggable delivery handler.

## How it works

When a campaign runs, Listmonk POSTs each message to a configured external URL. The API exposes:

```
POST /messenger/{handler_name}
```

The `handler_name` path segment selects which handler processes the message. Each handler maps to a separate messenger entry in Listmonk's settings, so routing is determined by which URL you configure there.

### Payload (sent by Listmonk)

```json
{
  "subject": "Welcome to our newsletter",
  "body": "<p>Hello {{ .Subscriber.Name }}</p>",
  "content_type": "html",
  "recipients": [
    {
      "uuid": "e44b4135-...",
      "email": "user@example.com",
      "name": "Jane Doe",
      "attribs": {
        "phone": "+1234567890",
        "fcm_id": "device-token-xyz"
      },
      "status": "enabled"
    }
  ],
  "campaign": {
    "uuid": "2e7e4b51-...",
    "name": "March Newsletter",
    "tags": ["newsletter", "march"]
  },
  "attachments": [
    { "url": "https://example.com/file.pdf", "name": "file.pdf" }
  ]
}
```

### Response

Return HTTP `200` to signal success. Any non-200 response causes Listmonk to retry according to its configured retry policy.

### Auth

The endpoint uses the same HTTP Basic Auth as the rest of the API (`LISTMONK_USER` / `LISTMONK_TOKEN`). Set these credentials in the Listmonk messenger configuration.

---

## Registered handlers

| Name | Path | Description |
|------|------|-------------|
| `fake` | `/messenger/fake` | No-op. Logs the message and returns 200. For development and testing. |

---

## Adding a new handler

### 1. Create the handler class

Create `app/handlers/<name>.py` implementing `MessengerHandlerBase`:

```python
# app/handlers/resend.py
import logging
from typing import override

import httpx

from app.handlers.base import MessengerHandlerBase
from app.schemas import MessengerPayload

logger = logging.getLogger(__name__)


class ResendHandler(MessengerHandlerBase):
    @override
    def send(self, payload: MessengerPayload) -> None:
        for recipient in payload.recipients:
            response = httpx.post(
                'https://api.resend.com/emails',
                headers={'Authorization': 'Bearer <RESEND_API_KEY>'},
                json={
                    'from': 'noreply@yourdomain.com',
                    'to': recipient.email,
                    'subject': payload.subject,
                    'html': payload.body,
                },
            )
            response.raise_for_status()
            logger.info('Resend: delivered to %s', recipient.email)
```

Rules:
- Return `None` on success.
- Raise any exception on failure — the router will propagate it as a 500, which causes Listmonk to retry.
- Access custom subscriber data via `recipient.attribs` (e.g., `recipient.attribs.get('phone')` for SMS).

### 2. Register it

Add one line to `app/handlers/__init__.py`:

```python
from app.handlers.resend import ResendHandler

HANDLERS: dict[str, type[MessengerHandlerBase]] = {
    'fake': FakeHandler,
    'resend': ResendHandler,   # ← add this
}
```

### 3. Configure Listmonk

In **Listmonk → Settings → Messengers**, add a new entry:

| Field | Value |
|-------|-------|
| Name | `monk-resend` (any label) |
| URL | `http://<api-host>/messenger/resend` |
| Username | value of `LISTMONK_USER` |
| Password | value of `LISTMONK_TOKEN` |

When creating a campaign, select `monk-resend` as the messenger.

### 4. Write a test

```python
# tests/test_messenger.py (add to existing file)

def test_resend_handler_returns_200(client, monkeypatch):
    # monkeypatch the external HTTP call so the test stays offline
    monkeypatch.setattr('app.handlers.resend.httpx.post', lambda *a, **kw: FakeResponse(200))
    response = client.post('/messenger/resend', json=VALID_PAYLOAD)
    assert response.status_code == HTTPStatus.OK
```

---

## File structure

```
app/
  handlers/
    __init__.py     # HANDLERS registry + get_handler() lookup
    base.py         # MessengerHandlerBase (ABC)
    fake.py         # FakeHandler — no-op, logs only
    resend.py       # example: email via Resend (not included)
  routers/
    messenger.py    # POST /messenger/{handler_name}
```
