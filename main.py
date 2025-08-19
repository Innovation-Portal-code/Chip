import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client
from app.routers.loop_webhook import router as loop_router
from app.routers.health import router as health_router
from app.routers.agent_test import router as agent_test_router

load_dotenv()

url: str | None = os.environ.get("SUPABASE_URL")
key: str | None = os.environ.get("SUPABASE_KEY")
supabase: Client | None = None
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
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!", "data": name}


# Include routers if available
if loop_router is not None:
    app.include_router(loop_router)

if health_router is not None:
    app.include_router(health_router)

if agent_test_router is not None:
    app.include_router(agent_test_router)
