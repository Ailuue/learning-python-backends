from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body:  str = Field(..., min_length=1)


class PostUpdate(BaseModel):
    title:     str | None  = Field(None, min_length=1, max_length=200)
    body:      str | None  = None
    published: bool | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    user_id:    int
    title:      str
    body:       str
    published:  bool
    created_at: datetime
