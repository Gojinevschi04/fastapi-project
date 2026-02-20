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


class UserUpdate(BaseModel):
    email: str | None = None
    role: UserRole | None = None


class UserResponse(BaseModel):
    id: int
    email: str | None
    role: UserRole
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    skip: int
    limit: int
