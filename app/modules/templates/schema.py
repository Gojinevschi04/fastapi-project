from datetime import datetime

from pydantic import BaseModel, field_validator


class TemplateBase(BaseModel):
    name: str
    base_script: str
    required_slots: list[str] = []

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be at most 100 characters")
        return v

    @field_validator("base_script")
    @classmethod
    def validate_base_script(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Base script must be at least 10 characters")
        if len(v) > 5000:
            raise ValueError("Base script must be at most 5000 characters")
        return v

    @field_validator("required_slots")
    @classmethod
    def validate_required_slots(cls, v: list[str]) -> list[str]:
        if len(v) > 20:
            raise ValueError("Maximum 20 required slots allowed")
        for slot in v:
            if not slot.strip():
                raise ValueError("Slot names cannot be empty")
            if len(slot) > 50:
                raise ValueError("Slot name must be at most 50 characters")
        return v


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = None
    base_script: str | None = None
    required_slots: list[str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Name must be at least 2 characters")
            if len(v) > 100:
                raise ValueError("Name must be at most 100 characters")
        return v

    @field_validator("base_script")
    @classmethod
    def validate_base_script(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < 10:
                raise ValueError("Base script must be at least 10 characters")
            if len(v) > 5000:
                raise ValueError("Base script must be at most 5000 characters")
        return v


class TemplateResponse(BaseModel):
    id: int
    name: str
    base_script: str
    required_slots: list[str]
    created_at: datetime
    updated_at: datetime
