from abc import ABC, abstractmethod

from app.schemas import MessengerPayload


class MessengerHandlerBase(ABC):
    @abstractmethod
    def send(self, payload: MessengerPayload) -> None:
        """Deliver the message. Raise on failure; return normally on success."""
        ...
