from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.schema import MessageResponse
from app.modules.templates.exceptions import TemplateInUseError, TemplateNameExistsError, TemplateNotFoundError
from app.modules.templates.schema import TemplateCreate, TemplateResponse, TemplateUpdate
from app.modules.templates.service import TemplateService
from app.modules.users.middleware import get_current_admin_user, get_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/", status_code=HTTPStatus.CREATED)
async def create_template_view(
    data: TemplateCreate,
    template_service: Annotated[TemplateService, Depends(TemplateService)],
    _current_user: Annotated[User, Depends(get_current_admin_user)],
) -> TemplateResponse:
    try:
        template = await template_service.create_template(data)
    except TemplateNameExistsError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e)) from e

    return TemplateResponse(
        id=template.id,
        name=template.name,
        base_script=template.base_script,
        required_slots=template.required_slots,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/")
async def get_templates_view(
    template_service: Annotated[TemplateService, Depends(TemplateService)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> list[TemplateResponse]:
    templates = await template_service.get_templates()
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            base_script=t.base_script,
            required_slots=t.required_slots,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in templates
    ]


@router.get("/{template_id}")
async def get_template_view(
    template_id: int,
    template_service: Annotated[TemplateService, Depends(TemplateService)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> TemplateResponse:
    try:
        template = await template_service.get_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e

    return TemplateResponse(
        id=template.id,
        name=template.name,
        base_script=template.base_script,
        required_slots=template.required_slots,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put("/{template_id}")
async def update_template_view(
    template_id: int,
    data: TemplateUpdate,
    template_service: Annotated[TemplateService, Depends(TemplateService)],
    _current_user: Annotated[User, Depends(get_current_admin_user)],
) -> TemplateResponse:
    try:
        template = await template_service.update_template(template_id, data)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except TemplateNameExistsError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e)) from e

    return TemplateResponse(
        id=template.id,
        name=template.name,
        base_script=template.base_script,
        required_slots=template.required_slots,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/{template_id}")
async def delete_template_view(
    template_id: int,
    template_service: Annotated[TemplateService, Depends(TemplateService)],
    _current_user: Annotated[User, Depends(get_current_admin_user)],
) -> MessageResponse:
    try:
        await template_service.delete_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except TemplateInUseError as e:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(e)) from e

    return MessageResponse(message="Template deleted successfully")
