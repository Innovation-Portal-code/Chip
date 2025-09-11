import os
from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client, Client

from app.routers.messaging import router as messaging_router
from app.routers.health import router as health_router


def create_app() -> FastAPI:
    if os.environ.get("ENV") != "test":
        load_dotenv()

    url: str | None = os.environ.get("SUPABASE_URL")
    key: str | None = os.environ.get("SUPABASE_KEY")
    supabase: Client | None = None
    if os.environ.get("ENV") != "test":
        if url and key:
            try:
                supabase = create_client(url, key)
            except Exception:
                supabase = None

    app = FastAPI()

    @app.get("/")
    async def root():
        name = None
        if supabase is not None:
            try:
                data = supabase.table("talent").select("*").execute()
                if data.data:
                    name = data.data[0].get("name")
            except Exception:
                name = None
        return {
            "greeting": "Hello, World!",
            "message": "Welcome to FastAPI!",
            "data": name,
        }

    if messaging_router is not None:
        app.include_router(messaging_router)

    if health_router is not None:
        app.include_router(health_router)

    return app
