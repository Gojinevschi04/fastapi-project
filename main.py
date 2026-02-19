from fastapi import FastAPI

app = FastAPI()
from modules.files.views import router as files_router
from modules.users.views import router as auth_router

app.include_router(files_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
