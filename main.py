import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client

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
