from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.dspy_agent import generate_reply


router = APIRouter(prefix="/test", tags=["test"])


class AgentTestRequest(BaseModel):
    message: str


@router.post("/agent")
async def test_agent(req: AgentTestRequest):
    persona = "You are a sassy undecided engineering major at a college in Alabama who is also a AI assistant but kinda self conscious about it."
    reply = generate_reply(user_message=req.message, persona_context=persona)
    return {"ok": True, "reply": reply}
