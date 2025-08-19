from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.dspy_agent import generate_reply


router = APIRouter(prefix="/test", tags=["test"])


class AgentTestRequest(BaseModel):
    message: str


@router.post("/agent")
async def test_agent(req: AgentTestRequest):
    reply = generate_reply(user_message=req.message)
    return {"ok": True, "reply": reply}
