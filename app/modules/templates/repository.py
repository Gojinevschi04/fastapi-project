from collections.abc import Sequence

from sqlmodel import func, select

from app.core.repositories import Repository
from app.modules.templates.models import DialogTemplate


class TemplateRepository(Repository):
    async def create(self, template: DialogTemplate) -> DialogTemplate:
        self._session.add(template)
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def get_by_id(self, template_id: int) -> DialogTemplate | None:
        result = await self._session.exec(select(DialogTemplate).where(DialogTemplate.id == template_id))
        return result.first()

    async def get_by_name(self, name: str) -> DialogTemplate | None:
        result = await self._session.exec(select(DialogTemplate).where(DialogTemplate.name == name))
        return result.first()

    async def get_all(self) -> Sequence[DialogTemplate]:
        result = await self._session.exec(select(DialogTemplate).order_by(DialogTemplate.name))
        return result.all()

    async def get_all_paginated(
        self, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[DialogTemplate], int]:
        query = select(DialogTemplate).order_by(DialogTemplate.name).offset(offset).limit(limit)
        result = await self._session.exec(query)
        templates = result.all()

        count_result = await self._session.exec(select(func.count()).select_from(DialogTemplate))
        total = count_result.one()

        return templates, total

    async def update(self, template: DialogTemplate) -> DialogTemplate:
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def delete(self, template_id: int) -> bool:
        template = await self.get_by_id(template_id)
        if not template:
            return False
        await self._session.delete(template)
        await self._session.commit()
        return True
