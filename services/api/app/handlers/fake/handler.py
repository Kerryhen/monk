from typing import override

from app.context import enrich_wide_event
from app.handlers.base import MessengerHandlerBase
from app.schemas import MessengerPayload


class FakeHandler(MessengerHandlerBase):
    received: list[MessengerPayload] = []

    @classmethod
    def clear(cls) -> None:
        cls.received.clear()

    @override
    def send(self, payload: MessengerPayload) -> None:
        self.received.append(payload)
        enrich_wide_event({
            'handler': 'fake',
            'campaign': payload.campaign.name,
            'subject': payload.subject,
            'recipients': len(payload.recipients),
        })
