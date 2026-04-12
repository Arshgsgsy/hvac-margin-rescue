from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from config import ANTHROPIC_API_KEY
from data_transformer import load_single_project
from llm_service import stream_chat

router = APIRouter()


class ChatRequest(BaseModel):
    project_id: str
    question: str


@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        project = load_single_project(req.project_id)
    except RuntimeError as exc:
        raise HTTPException(500, str(exc)) from exc

    if not project:
        raise HTTPException(404, f"Project '{req.project_id}' not found")
    if not ANTHROPIC_API_KEY:
        raise HTTPException(503, "ANTHROPIC_API_KEY is not configured.")

    return StreamingResponse(
        stream_chat(project, req.question),
        media_type="text/plain; charset=utf-8",
    )
