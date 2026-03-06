import logging
from typing import override

from app.handlers.base import MessengerHandlerBase
from app.schemas import MessengerPayload

logger = logging.getLogger(__name__)


class FakeHandler(MessengerHandlerBase):
    received: list[MessengerPayload] = []

    @classmethod
    def clear(cls) -> None:
        cls.received.clear()

    @override
    def send(self, payload: MessengerPayload) -> None:
        self.received.append(payload)
        logger.info(
            'fake_handler.send',
            extra={
                'campaign': payload.campaign.name,
                'subject': payload.subject,
                'recipients': len(payload.recipients),
            },
        )
