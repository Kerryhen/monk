from pydantic import BaseModel


class ChatwootButtonParam(BaseModel):
    type: str
    parameter: str  # resolver ref
    url: str
    variables: list[str]


class ChatwootTemplateParams(BaseModel):
    body: dict[str, str]  # slot_id -> resolver ref
    buttons: list[ChatwootButtonParam] = []


class ChatwootTemplateConfig(BaseModel):
    template_name: str
    language: str
    category: str
    params: ChatwootTemplateParams
