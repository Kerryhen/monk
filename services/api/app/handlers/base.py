from abc import ABC, abstractmethod

from app.schemas import MessengerPayload


class MessengerHandlerBase(ABC):
    @abstractmethod
    def send(self, payload: MessengerPayload) -> None:
        """Deliver the message. Raise on failure; return normally on success."""
        ...


class TemplateProviderBase(ABC):
    @abstractmethod
    def get_templates(self) -> list[dict]:
        """Return list of available templates."""
        ...


class SchemaProviderBase(ABC):
    @abstractmethod
    def get_schemas(self) -> dict[str, dict]:
        """Return all schemas keyed by source name."""
        ...

    @abstractmethod
    def get_schema(self, name: str) -> dict:
        """Return schema for the given source name. Raise KeyError if not found."""
        ...


class VariableResolverBase(ABC):
    @abstractmethod
    def resolve(self, ref: str, context: dict) -> tuple[bool, str]:
        """Resolve a template variable reference against context.

        Returns (ok, value). ok=False means a required field was absent.
        """
        ...
