from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict
from loguru import logger

from tools.local_llm import get_local_llm, LocalLLMUnavailable

router = APIRouter(prefix="/api/llm", tags=["Local LLM"])


class Msg(BaseModel):
    role: str
    content: str


class LocalChatRequest(BaseModel):
    messages: List[Msg]
    temperature: float = 0.7


@router.post("/local_stream")
async def local_stream(req: LocalChatRequest):
    try:
        llm = get_local_llm()
    except LocalLLMUnavailable as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

    def token_stream():
        for token in llm.stream_chat([m.dict() for m in req.messages], req.temperature):
            yield token

    return StreamingResponse(token_stream(), media_type="text/plain")


