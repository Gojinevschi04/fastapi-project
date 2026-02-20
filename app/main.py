from fastapi import FastAPI

from app.modules.files.views import router as files_router
from app.modules.users.views import router as auth_router

app = FastAPI()


app.include_router(files_router)
app.include_router(auth_router)
