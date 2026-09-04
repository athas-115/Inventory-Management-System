"""User schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for creating a user (from GitHub OAuth)."""
    github_id: int
    username: str
    email: str | None = None
    avatar_url: str | None = None
    display_name: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: EmailStr | None = None
    display_name: str | None = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    github_id: int
    username: str
    email: str | None = None
    avatar_url: str | None = None
    display_name: str | None = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
