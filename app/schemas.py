from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ListSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    uuid: str
    name: str
    optin: str
    status: str
    tags: List[str]
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
    data: ListSchema


class ListsSchema(BaseModel):
    results: List[ListSchema]


class MonkListsSchema(BaseModel):
    data: ListsSchema
    total: int
    per_page: int
    page: int


class CreateListSchema(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., description='Name of the new list')
    type: Literal['private', 'public']
    optin: Literal['single', 'double']
    status: Literal['active', 'archived'] = 'active'
    tags: Optional[List[str]]  = None
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
