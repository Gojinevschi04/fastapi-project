from datetime import datetime

from pydantic import BaseModel


class TemplateBase(BaseModel):
    name: str
    base_script: str
    required_slots: list[str] = []


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = None
    base_script: str | None = None
    required_slots: list[str] | None = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    base_script: str
    required_slots: list[str]
    created_at: datetime
    updated_at: datetime
