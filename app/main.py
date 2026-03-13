from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.health import router as health_router
from app.core.middleware import RequestLoggingMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.modules.admin.views import router as admin_router
from app.modules.auth.views import router as auth_router
from app.modules.calls.views import router as calls_router
from app.modules.files.views import router as files_router
from app.modules.tasks.views import router as tasks_router
from app.modules.templates.views import router as templates_router
from app.modules.users.views import router as users_router
from app.modules.webhooks.views import router as webhooks_router


def get_application() -> FastAPI:
    app = FastAPI(
        title="Quiet Call AI",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — configurable origins
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting
    app.add_middleware(RateLimitMiddleware)

    # Routers
    app.include_router(health_router)
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
