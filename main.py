from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.loop_webhook import router as loop_router

app = FastAPI()


@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}


app.include_router(health_router)
app.include_router(loop_router)
