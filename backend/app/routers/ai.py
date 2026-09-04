import os
import sys

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/api/ai", tags=["AI"])


class AIRequest(BaseModel):
    message: str


# Make the ai_agent directory importable
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

AI_AGENT_PATH = None

for _ in range(5):
    candidate = os.path.join(CURRENT_DIR, "ai_agent")

    if os.path.isdir(candidate):
        AI_AGENT_PATH = candidate
        break

    CURRENT_DIR = os.path.dirname(CURRENT_DIR)

if AI_AGENT_PATH is None:
    raise RuntimeError("Could not locate the ai_agent directory")

if AI_AGENT_PATH not in sys.path:
    sys.path.insert(0, AI_AGENT_PATH)


from agent import ask_inventory_ai, create_ai_client


@router.post("/ask")
async def ask_ai(
    request: AIRequest,
    current_user: User = Depends(get_current_user),
):
    mcp_client = None

    try:
        mcp_client, groq, tools = await create_ai_client()

        response = await ask_inventory_ai(
            request.message,
            mcp_client,
            groq,
            tools,
        )

        return {
            "response": response,
        }

    finally:
        if mcp_client:
            await mcp_client.cleanup()