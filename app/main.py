from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.modules.files.views import router as files_router
from app.modules.users.views import router as auth_router


def get_application() -> FastAPI:
    app = FastAPI(title="FastAPIProject", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(files_router)
    app.include_router(auth_router)

    return app


app = get_application()
