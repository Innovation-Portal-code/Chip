from fastapi import APIRouter
from pydantic import BaseModel

from app.agents import dspy_agent as agent_module


router = APIRouter(prefix="/test", tags=["test"])


class AgentTestRequest(BaseModel):
    message: str


@router.post("/agent")
async def test_agent(req: AgentTestRequest):
    reply = agent_module.generate_reply(user_message=req.message)
    return {"ok": True, "reply": reply}
