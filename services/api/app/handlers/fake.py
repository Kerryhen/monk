import logging
from typing import override

from app.handlers.base import MessengerHandlerBase
from app.schemas import MessengerPayload

logger = logging.getLogger(__name__)


class FakeHandler(MessengerHandlerBase):
    @override
    def send(self, payload: MessengerPayload) -> None:
        logger.info(
            'FakeHandler: campaign=%r subject=%r recipients=%d',
            payload.campaign.name,
            payload.subject,
            len(payload.recipients),
        )
