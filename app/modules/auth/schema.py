import re

from pydantic import BaseModel, EmailStr, field_validator

from app.core.constants import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) > PASSWORD_MAX_LENGTH:
            raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters")
        return v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        if len(v) > PASSWORD_MAX_LENGTH:
            raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not PHONE_REGEX.match(v):
            raise ValueError("Invalid phone number format")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        if len(v) > PASSWORD_MAX_LENGTH:
            raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters")
        return v
