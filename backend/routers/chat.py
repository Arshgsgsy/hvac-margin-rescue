from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from data_transformer import load_single_project
from llm_service import stream_chat

router = APIRouter()


class ChatRequest(BaseModel):
    project_id: str
    question: str


@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    project = load_single_project(req.project_id)
    if not project:
        raise HTTPException(404, f"Project '{req.project_id}' not found")

    return StreamingResponse(
        stream_chat(project, req.question),
        media_type="text/plain; charset=utf-8",
    )
