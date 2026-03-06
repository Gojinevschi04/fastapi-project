from sqlalchemy import JSON
from sqlmodel import Column, Field

from app.core.models import BaseModel


class DialogTemplate(BaseModel, table=True):
    __tablename__ = "dialog_template"

    name: str = Field(index=True, nullable=False)
    base_script: str = Field(nullable=False)
    required_slots: list[str] = Field(default=[], sa_column=Column(JSON, nullable=False))
