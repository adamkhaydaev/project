from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class URLBase(BaseModel):
    original_url: str
    expiration_days: Optional[int] = None


class URLCreate(URLBase):
    pass


class URLCreateResponse(URLBase):
    id: int
    alias: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class URLList(URLCreateResponse):
    is_active: bool
    clicks_count: int


class URLStats(BaseModel):
    alias: str
    original_url: str
    clicks_count: int
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True
