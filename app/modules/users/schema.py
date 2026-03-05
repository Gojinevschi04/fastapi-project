from enum import StrEnum

from pydantic import BaseModel


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserInfo(BaseModel):
    id: int
    email: str | None
    role: UserRole


class UserCreate(BaseModel):
    email: str
    role: UserRole = UserRole.USER
    password: str
    phone_number: str | None = None


class UserUpdate(BaseModel):
    email: str | None = None
    role: UserRole | None = None
    phone_number: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str | None
    role: UserRole
    phone_number: str | None = None
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    skip: int
    limit: int


class ProfileUpdate(BaseModel):
    phone_number: str | None = None
    email: str | None = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
