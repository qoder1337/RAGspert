from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None


# User-Response (without Password)
class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
