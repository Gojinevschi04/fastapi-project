from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class FileType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"


class FileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    file_type: FileType
    user_id: int
    content_hash: str | None = None


class FileCreate(FileBase):
    pass


class FileUpdate(BaseModel):
    content_hash: str | None = None


class FileResponse(BaseModel):
    id: int
    original_filename: str
    file_size: int
    file_type: FileType
    created_at: datetime
    updated_at: datetime
    download_url: str | None = None


class FileContentResponse(BaseModel):
    content: bytes
    original_filename: str
    content_type: str
