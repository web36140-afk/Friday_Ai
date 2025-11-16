"""
Chat API V2 - Stateless, Simple, PROVEN
Based on Claude/ChatGPT architecture
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator
from loguru import logger
import uuid
import json

from core.conversation_store import conversation_store
from core.llm_engine import llm_engine
from config import settings

router = APIRouter()


class MessageItem(BaseModel):
    role: str
    content: str


class ChatV2Request(BaseModel):
    messages: List[MessageItem]  # Full conversation history from frontend
    conversation_id: Optional[str] = None
    language: str = "en-US"
    temperature: float = 0.7
    # Provider auto-selected by backend based on language


async def stream_v2(request: ChatV2Request) -> AsyncGenerator[str, None]:
    """
    Simple streaming - Frontend sends FULL history
    Backend just processes and returns response
    """
    
    # Get or create conversation ID
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    logger.error(f"")
    logger.error(f"{'='*70}")
    logger.error(f"💬 CHAT V2 REQUEST")
    logger.error(f"   Conversation ID: {conv_id}")
    logger.error(f"   Messages from frontend: {len(request.messages)}")
    logger.error(f"   Last message: {request.messages[-1].content[:50] if request.messages else 'None'}")
    
    # Log full conversation
    for i, msg in enumerate(request.messages, 1):
        logger.error(f"   {i}. [{msg.role}]: {msg.content[:60]}")
    logger.error(f"{'='*70}")
    
    # Convert messages
    from models.schemas import Message
    from datetime import datetime
    
    history_msgs = [
        Message(role=msg.role, content=msg.content, timestamp=datetime.now())
        for msg in request.messages[:-1]  # All except last (current question)
    ]
    
    current_question = request.messages[-1].content
    
    # SIMPLE CONTEXT FIX: If short question, find last topic and rewrite
    if len(current_question.strip()) < 30 and len(history_msgs) >= 1:
        last_topic = None
        import re
        
        for msg in reversed(request.messages[:-1]):
            if msg.role == 'user':
                # Find proper nouns
                caps = re.findall(r'\b[A-Z][a-z]+\b', msg.content)
                if caps:
                    last_topic = caps[-1]
                    break
                # Devanagari
                if 'नेपाल' in msg.content or 'nepal' in msg.content.lower():
                    last_topic = 'Nepal'
                    break
                if 'काठमाडौं' in msg.content or 'kathmandu' in msg.content.lower():
                    last_topic = 'Kathmandu'
                    break
        
        if last_topic:
            original = current_question
            current_question = f"{original} of {last_topic}"
            logger.error(f"🔴 REWRITTEN: '{original}' → '{current_question}'")
    
    # Stream from LLM with FULL history
    full_response = ""
    
    # Provider auto-selected by llm_engine based on language
    async for chunk in llm_engine.stream_chat(
        message=current_question,
        history=history_msgs,
        temperature=request.temperature,
        language=request.language
    ):
        if chunk.get("type") == "token":
            content = chunk.get("content", "")
            full_response += content
            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
    
    # Save to store
    conversation_store.add_message(conv_id, "user", request.messages[-1].content)
    conversation_store.add_message(conv_id, "assistant", full_response)
    
    # Send conversation ID and done
    yield f"data: {json.dumps({'type': 'conversation_id', 'id': conv_id})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/v2/stream")
async def chat_v2_stream(request: ChatV2Request):
    """
    V2 Streaming endpoint - Frontend sends full history
    STATELESS - No server-side conversation management
    """
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    return StreamingResponse(
        stream_v2(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Conversation-ID": conv_id
        }
    )


@router.get("/v2/test")
async def test_v2():
    """Test endpoint"""
    return {
        "version": "2.0",
        "method": "stateless",
        "conversations_in_store": len(conversation_store.get_all_ids())
    }

