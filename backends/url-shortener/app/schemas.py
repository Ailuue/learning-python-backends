from datetime import datetime

from pydantic import BaseModel, field_validator


class URLCreate(BaseModel):
    original_url: str
    custom_code: str | None = None
    expires_at: datetime | None = None

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: str | None) -> str | None:
        if v is not None and (not v.isalnum() or not (3 <= len(v) <= 10)):
            raise ValueError("Custom code must be 3–10 alphanumeric characters")
        return v


class URLResponse(BaseModel):
    id: int
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: datetime | None = None
    click_count: int
    is_active: bool

    model_config = {"from_attributes": True}


class URLStats(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool


class URLListResponse(BaseModel):
    items: list[URLResponse]
    total: int
    page: int
    page_size: int
