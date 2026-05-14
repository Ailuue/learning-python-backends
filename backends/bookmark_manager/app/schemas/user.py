from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)


class UserPublic(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
