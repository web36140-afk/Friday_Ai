"""
ULTRA-SIMPLE Chat API
Guarantees conversation continuity
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator, Optional
from loguru import logger

from core.simple_conversation import simple_conversation
from core.llm_engine import llm_engine
from models.schemas import Message

router = APIRouter()


class SimpleChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    language: str = "en-US"


async def simple_stream(request: SimpleChatRequest) -> AsyncGenerator[str, None]:
    """Simple streaming that GUARANTEES context"""
    
    # Get or create conversation
    conv_id = simple_conversation.get_or_create_conversation(request.conversation_id)
    
    # Add user message
    simple_conversation.add_message("user", request.message)
    
    # Get history
    history = simple_conversation.get_history()
    
    # Convert to Message objects
    history_msgs = [
        Message(role=msg['role'], content=msg['content'], timestamp=msg.get('timestamp'))
        for msg in history[:-1]  # Exclude the message we just added
    ]
    
    logger.warning(f"📨 STREAMING - Conv: {conv_id}, History: {len(history_msgs)} msgs")
    
    # Stream from LLM
    full_response = ""
    
    # Use Groq (free, fast, works perfectly)
    async for chunk in llm_engine.stream_chat(
        message=request.message,
        history=history_msgs,
        provider="groq",
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        language=request.language
    ):
        if chunk.get("type") == "token":
            content = chunk.get("content", "")
            full_response += content
            yield f"data: {{'type': 'token', 'content': {json.dumps(content)}}}\n\n"
    
    # Save assistant response
    simple_conversation.add_message("assistant", full_response)
    
    # Send conversation ID
    yield f"data: {{'type': 'conversation_id', 'id': '{conv_id}'}}\n\n"
    yield f"data: {{'type': 'done'}}\n\n"


@router.post("/simple/stream")
async def chat_simple_stream(request: SimpleChatRequest):
    """Ultra-simple streaming endpoint"""
    return StreamingResponse(
        simple_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Conversation-ID": simple_conversation.active_conversation_id or "new"
        }
    )


@router.post("/simple/new")
async def start_new_chat():
    """Start a brand new conversation"""
    conv_id = simple_conversation.start_new_conversation()
    return {"conversation_id": conv_id, "message": "New conversation started"}


@router.get("/simple/history")
async def get_simple_history():
    """Get current conversation history"""
    return {
        "conversation_id": simple_conversation.active_conversation_id,
        "messages": simple_conversation.get_history(),
        "total": len(simple_conversation.messages)
    }


import json

