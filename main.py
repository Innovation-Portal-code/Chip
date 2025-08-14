import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client
from app.routers.loop_webhook import router as loop_router
from app.routers.health import router as health_router
from app.routers.agent_test import router as agent_test_router

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()


@app.get("/")
async def root():
    data = supabase.table("talent").select("*").execute()
    print(data.data[0]["name"])
    return {
        "greeting": "Hello, World!",
        "message": "Welcome to FastAPI!",
        "data": data.data[0]["name"],
    }


# Include routers if available
if loop_router is not None:
    app.include_router(loop_router)

if health_router is not None:
    app.include_router(health_router)

if agent_test_router is not None:
    app.include_router(agent_test_router)
