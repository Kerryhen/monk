from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ListSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    uuid: str
    name: str
    type: str
    optin: str
    status: str
    tags: List[str]
    description: Optional[str] = None
    subscriber_count: int


class UpdateListSchema(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: Optional[str] = None
    type: Optional[str] = None
    optin: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None


class ResponseUpdateListSchema(BaseModel):
    data: UpdateListSchema


class ListsSchema(BaseModel):
    results: List[ListSchema]


class MonkListsSchema(BaseModel):
    data: ListsSchema
    total: int
    per_page: int
    page: int


class CreateListSchema(BaseModel):
    name: str = Field(..., description='Name of the new list')
    type: Literal['private', 'public']
    optin: Literal['single', 'double']
    status: Literal['active', 'archived'] = 'active'
    tags: Optional[List[str]] = None
    description: Optional[str] = None


class DeleteListSchema(BaseModel):
    id: Optional[List[int]] = None
    query: Optional[str] = None

    @model_validator(mode='after')
    def validate_id_or_query(self):
        if not self.id and not self.query:
            raise ValueError("Either 'id' or 'query' must be provided")

        if self.id and self.query:
            raise ValueError("Provide only one of 'id' or 'query', not both")

        return self


class DeleteListResonseSchema(BaseModel):
    data: bool


class MonkCampaingCreate(BaseModel):
    name: str = Field(..., description='Campaign name')
    subject: str = Field(..., description='Campaign email subject')
    lists: List[int] = Field(..., description='List IDs to send campaign to')

    from_email: Optional[str] = Field(None, description="'From' email in campaign emails")

    type: Literal['regular', 'optin'] = Field(..., description='Campaign type')

    content_type: Literal['richtext', 'html', 'markdown', 'plain', 'visual'] = Field(..., description='Content type')

    body: str = Field(..., description='Content body of campaign')

    body_source: Optional[Dict[str, Any]] = Field(None, description='JSON block source of the body (if content_type is visual)')

    altbody: Optional[str] = Field(None, description='Alternate plain text body for HTML or richtext emails')

    send_at: Optional[datetime] = Field(None, description='Schedule timestamp (ISO 8601, e.g. 2024-01-01T12:00:00Z)')

    messenger: Optional[str] = Field('email', description="Messenger type, defaults to 'email'")

    template_id: Optional[int] = Field(None, description='Template ID to use')

    tags: Optional[List[str]] = Field(None, description='Tags to mark campaign')

    headers: Optional[List[Dict[str, str]]] = Field(None, description='SMTP headers as key-value pairs')

    attribs: Optional[Dict[str, Any]] = Field(None, description='Optional JSON attributes for template usage')


class InterfaceCampaingCreate(MonkCampaingCreate):
    lists: List[str] = Field(..., description='List IDs to send campaign to')


class PBMonkListSchema(BaseModel):
    id: str
    created: datetime
    updated: datetime


class PBMonkClientListSchema(BaseModel):
    id: str
    client: str
    lists: List[str]  # list of monk_list IDs
    created: datetime
    updated: datetime
