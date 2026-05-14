from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.tag import TagPublic


class BookmarkBase(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=1000)
    favorite: bool = False
    category_id: int | None = None


class BookmarkCreate(BookmarkBase):
    tags: list[str] = Field(default_factory=list, max_length=20)


class BookmarkUpdate(BaseModel):
    url: HttpUrl | None = None
    title: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=1000)
    favorite: bool | None = None
    category_id: int | None = None
    tags: list[str] | None = Field(default=None, max_length=20)


class BookmarkPublic(BaseModel):
    id: int
    url: str
    title: str
    description: str | None
    favorite: bool
    click_count: int
    category_id: int | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagPublic] = []

    model_config = ConfigDict(from_attributes=True)
