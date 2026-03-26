from typing import Any, override

from pydantic import BaseModel, ConfigDict

from app.handlers.base import SchemaProviderBase


class LeadContext(BaseModel):
    """Fields available under `lead.*` in template variable references."""

    uuid: str
    email: str
    name: str
    status: str
    attribs: dict[str, Any]


class CampaignContext(BaseModel):
    """Fields available under `campanha.*` in template variable references."""

    uuid: str
    name: str
    subject: str
    tags: list[str]


class InstanciaContext(BaseModel):
    """Fields available under `instancia.*` — schema pending P-02 resolution."""

    model_config = ConfigDict(extra='allow')


_SCHEMAS: dict[str, type[BaseModel]] = {
    'lead': LeadContext,
    'campanha': CampaignContext,
    'instancia': InstanciaContext,
}


class ChatwootSchemaProvider(SchemaProviderBase):
    @override
    def get_schemas(self) -> dict[str, dict]:
        return {name: model.model_json_schema() for name, model in _SCHEMAS.items()}

    @override
    def get_schema(self, name: str) -> dict:
        model = _SCHEMAS.get(name)
        if model is None:
            raise KeyError(name)
        return model.model_json_schema()
