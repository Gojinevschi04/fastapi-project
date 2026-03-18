from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.constants import (
    MAX_SLOT_COUNT,
    MAX_SLOT_KEY_LENGTH,
    TEMPLATE_NAME_MAX_LENGTH,
    TEMPLATE_NAME_MIN_LENGTH,
    TEMPLATE_SCRIPT_MAX_LENGTH,
    TEMPLATE_SCRIPT_MIN_LENGTH,
)

SUPPORTED_LANGUAGES = ("en", "ru", "ro")


class TemplateBase(BaseModel):
    name: str
    base_script: str
    required_slots: list[str] = []
    language: str = "en"

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Language must be one of: {', '.join(SUPPORTED_LANGUAGES)}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < TEMPLATE_NAME_MIN_LENGTH:
            raise ValueError(f"Name must be at least {TEMPLATE_NAME_MIN_LENGTH} characters")
        if len(v) > TEMPLATE_NAME_MAX_LENGTH:
            raise ValueError(f"Name must be at most {TEMPLATE_NAME_MAX_LENGTH} characters")
        return v

    @field_validator("base_script")
    @classmethod
    def validate_base_script(cls, v: str) -> str:
        v = v.strip()
        if len(v) < TEMPLATE_SCRIPT_MIN_LENGTH:
            raise ValueError(f"Base script must be at least {TEMPLATE_SCRIPT_MIN_LENGTH} characters")
        if len(v) > TEMPLATE_SCRIPT_MAX_LENGTH:
            raise ValueError(f"Base script must be at most {TEMPLATE_SCRIPT_MAX_LENGTH} characters")
        return v

    @field_validator("required_slots")
    @classmethod
    def validate_required_slots(cls, v: list[str]) -> list[str]:
        if len(v) > MAX_SLOT_COUNT:
            raise ValueError(f"Maximum {MAX_SLOT_COUNT} required slots allowed")
        for slot in v:
            if not slot.strip():
                raise ValueError("Slot names cannot be empty")
            if len(slot) > MAX_SLOT_KEY_LENGTH:
                raise ValueError(f"Slot name must be at most {MAX_SLOT_KEY_LENGTH} characters")
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
            if len(v) < TEMPLATE_NAME_MIN_LENGTH:
                raise ValueError(f"Name must be at least {TEMPLATE_NAME_MIN_LENGTH} characters")
            if len(v) > TEMPLATE_NAME_MAX_LENGTH:
                raise ValueError(f"Name must be at most {TEMPLATE_NAME_MAX_LENGTH} characters")
        return v

    @field_validator("base_script")
    @classmethod
    def validate_base_script(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < TEMPLATE_SCRIPT_MIN_LENGTH:
                raise ValueError(f"Base script must be at least {TEMPLATE_SCRIPT_MIN_LENGTH} characters")
            if len(v) > TEMPLATE_SCRIPT_MAX_LENGTH:
                raise ValueError(f"Base script must be at most {TEMPLATE_SCRIPT_MAX_LENGTH} characters")
        return v


class TemplateResponse(BaseModel):
    id: int
    name: str
    base_script: str
    required_slots: list[str]
    language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
