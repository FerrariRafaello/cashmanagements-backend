# IMPORTS
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    name: str
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Lowercase and strip whitespace from email."""
        return v.strip().lower()

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Strip whitespace from name."""
        return v.strip()


class UserCreate(UserBase):
    """
    Used for registration - receives the pain password."""
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Enforces minimum password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number.")
        return v

class UserUpdate(BaseModel):
    """Used for account settings - all fields optional"""
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class LoginRequest(BaseModel):
    """Used for login - only email and password, no strength validation."""
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Lowercase and strip whitespace from email."""
        return v.strip().lower()

class UserResponse(UserBase):
    """Returned to the client - never exposes the password."""
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes =  True


class TokenResponse(BaseModel):
    """Returned after succesfull login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from the JWT payload."""
    user_id: UUID
