import os
from fastapi import FastAPI
from dotenv import load_dotenv

from app.routers.messaging import router as messaging_router
from app.routers.health import router as health_router
from app.observability import configure_observability


def create_app() -> FastAPI:
    if os.environ.get("ENV") != "test":
        load_dotenv()

    app = FastAPI()

    # Observability (Logfire, correlation IDs)
    configure_observability(app)

    @app.get("/")
    async def root():
        return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

    if messaging_router is not None:
        app.include_router(messaging_router)

    if health_router is not None:
        app.include_router(health_router)

    return app
