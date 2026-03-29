"""FastAPI routes for the City Explorer backend.

Provides:
- POST /chat/stream - SSE streaming chat endpoint
- GET /health - Health check endpoint
"""

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add src/ to Python path for agent imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.agent import run_agent_streaming, get_skill_info
from agent.skills import DEFAULT_SKILL

from .session_manager import session_manager


router = APIRouter()


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str
    session_id: str | None = None
    skill_id: str = DEFAULT_SKILL


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming chat endpoint.

    Emits events in the following format:
    - session: {"type": "session", "session_id": "uuid"}
    - skill: {"type": "skill", "name": "...", "description": "..."}
    - text: {"type": "text", "content": "..."}
    - tools: {"type": "tools", "tools": [...]}
    - end: {"type": "end"}
    """

    def generate():
        # Get or create session
        session = session_manager.get_or_create_session(request.session_id)

        # Emit session ID
        yield f"data: {json.dumps({'type': 'session', 'session_id': session.session_id})}\n\n"

        # Emit skill info
        skill = get_skill_info(request.skill_id)
        yield f"data: {json.dumps({'type': 'skill', 'name': skill.name, 'description': skill.description})}\n\n"

        # Collect tool calls
        tool_calls: list[dict[str, Any]] = []

        def on_tool_call(name: str, args: dict):
            tool_calls.append({"tool_name": name, "args": args})

        # Run the agent with streaming
        try:
            gen = run_agent_streaming(
                user_message=request.message,
                conversation_history=session.conversation_history,
                skill_id=request.skill_id,
                on_tool_call=on_tool_call,
            )

            # Stream text chunks
            for chunk in gen:
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # Emit tools used
        if tool_calls:
            yield f"data: {json.dumps({'type': 'tools', 'tools': tool_calls})}\n\n"

        # End stream
        yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "api": True,
    }
