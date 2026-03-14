import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.modules.admin.views import router as admin_router
from app.modules.auth.views import router as auth_router
from app.modules.calls.views import router as calls_router
from app.modules.files.views import router as files_router
from app.modules.scheduler.service import run_scheduler
from app.modules.tasks.views import router as tasks_router
from app.modules.templates.views import router as templates_router
from app.modules.users.views import router as users_router
from app.modules.webhooks.views import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    scheduler_task = asyncio.create_task(run_scheduler())
    yield
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


def get_application() -> FastAPI:
    app = FastAPI(title="Quiet Call AI", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(files_router)
    app.include_router(templates_router)
    app.include_router(tasks_router)
    app.include_router(calls_router)
    app.include_router(admin_router)
    app.include_router(webhooks_router)

    return app


app = get_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
