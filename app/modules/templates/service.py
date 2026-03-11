from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends

from app.core.logging import get_logger
from sqlalchemy.exc import IntegrityError

from app.modules.templates.exceptions import TemplateInUseError, TemplateNameExistsError, TemplateNotFoundError
from app.modules.templates.models import DialogTemplate
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schema import TemplateCreate, TemplateUpdate

logger = get_logger(__name__)


class TemplateService:
    def __init__(
        self,
        template_repository: Annotated[TemplateRepository, Depends(TemplateRepository)],
    ) -> None:
        self.template_repository = template_repository

    async def create_template(self, data: TemplateCreate) -> DialogTemplate:
        existing = await self.template_repository.get_by_name(data.name)
        if existing:
            raise TemplateNameExistsError(f"Template with name '{data.name}' already exists")

        template = DialogTemplate(
            name=data.name,
            base_script=data.base_script,
            required_slots=data.required_slots,
        )
        return await self.template_repository.create(template)

    async def get_template(self, template_id: int) -> DialogTemplate:
        template = await self.template_repository.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template with id {template_id} not found")
        return template

    async def get_templates(self, limit: int = 50, offset: int = 0) -> Sequence[DialogTemplate]:
        templates, _ = await self.template_repository.get_all_paginated(limit, offset)
        return templates

    async def update_template(self, template_id: int, data: TemplateUpdate) -> DialogTemplate:
        template = await self.template_repository.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template with id {template_id} not found")

        if data.name is not None:
            existing = await self.template_repository.get_by_name(data.name)
            if existing and existing.id != template_id:
                raise TemplateNameExistsError(f"Template with name '{data.name}' already exists")
            template.name = data.name
        if data.base_script is not None:
            template.base_script = data.base_script
        if data.required_slots is not None:
            template.required_slots = data.required_slots

        return await self.template_repository.update(template)

    async def delete_template(self, template_id: int) -> bool:
        template = await self.template_repository.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template with id {template_id} not found")
        try:
            return await self.template_repository.delete(template_id)
        except IntegrityError as e:
            raise TemplateInUseError(
                f"Template '{template.name}' cannot be deleted because it is used by existing tasks"
            ) from e
