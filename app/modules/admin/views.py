from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.admin.service import AdminService
from app.modules.tasks.schema import AdminStatsResponse
from app.modules.users.middleware import get_current_admin_user
from app.modules.users.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_admin_stats_view(
    admin_service: Annotated[AdminService, Depends(AdminService)],
    _current_user: Annotated[User, Depends(get_current_admin_user)],
) -> AdminStatsResponse:
    return await admin_service.get_system_stats()
