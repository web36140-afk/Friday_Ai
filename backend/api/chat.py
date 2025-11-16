"""
Chat API endpoints with streaming support
"""
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from models.schemas import ChatRequest, ChatResponse, StreamChunk
from core.llm_engine import llm_engine
from core.memory import memory_manager
from core.learning_system import learning_system
from core.tool_manager import tool_manager
from core.model_router import model_router
from core.context_tracker import context_tracker
from core.context_resolver import context_resolver
from core.auto_tool_caller import auto_tool_caller
from core.followup_generator import followup_generator
from core.semantic_memory import semantic_memory
from core.langchain_memory import langchain_memory
from config import settings, SYSTEM_PROMPT

router = APIRouter()


async def stream_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Generate streaming response chunks"""
    try:
        # CRITICAL DEBUG
        logger.error(f"")
        logger.error(f"{'='*60}")
        logger.error(f"📥 STREAM REQUEST RECEIVED")
        logger.error(f"   conversation_id from frontend: {request.conversation_id}")
        logger.error(f"   message: {request.message[:50]}")
        logger.error(f"{'='*60}")
        
        # Get or create conversation
        conversation = await memory_manager.get_or_create_conversation(
            conversation_id=request.conversation_id,
            project_id=request.project_id
        )
        
        logger.error(f"📌 CONVERSATION OBJECT RETURNED:")
        logger.error(f"   ID: {conversation.id}")
        logger.error(f"   Messages count: {len(conversation.messages)}")
        logger.error(f"   Is it SAME as frontend sent? {conversation.id == request.conversation_id}")
        logger.error(f"{'='*60}")
        
        # NOTE: We add the ORIGINAL message to history first
        # But we'll send the RESOLVED version to the LLM
        await memory_manager.add_message(
            conversation.id,
            role="user",
            content=request.message  # Store original message
        )
        
        # Get FULL conversation history for context awareness
        # This ensures FRIDAY remembers everything from the conversation
        history = await memory_manager.get_conversation_history(
            conversation.id,
            limit=settings.max_conversation_history
        )
        
        is_new_conversation = len(history) <= 1  # Only user message exists
        logger.info(f"💭 Conversation {conversation.id}")
        logger.info(f"   → New: {is_new_conversation} | History: {len(history)} messages")
        
        # DEBUG: Log FULL conversation history for troubleshooting
        logger.warning(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.warning(f"🔍 CONVERSATION HISTORY CHECK:")
        logger.warning(f"   Conversation ID: {conversation.id}")
        logger.warning(f"   Total messages in history: {len(history)}")
        
        if len(history) > 0:
            logger.warning(f"   📜 ALL Messages in this conversation:")
            for i, msg in enumerate(history, 1):
                logger.warning(f"      {i}. [{msg.role}]: {msg.content[:80]}")
        else:
            logger.error(f"   ❌ HISTORY IS EMPTY! This is the problem!")
        
        logger.warning(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Extract context for intelligent routing
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in history[-10:]
            if msg.role in ["user", "assistant"]
        ]
        context_info = context_tracker.extract_context(history_dicts)
        
        # PERPLEXITY'S METHOD: Just rewrite the damn question
        actual_question = request.message
        
        # If short question (< 30 chars), find last topic and REWRITE
        if len(request.message.strip()) < 30 and len(history_dicts) >= 2:
            last_topic = None
            
            # Find last topic from history
            for msg in reversed(history_dicts):
                if msg['role'] == 'user':
                    import re
                    # English
                    caps = re.findall(r'\b[A-Z][a-z]+\b', msg['content'])
                    if caps:
                        last_topic = caps[-1]
                        break
                    # Devanagari
                    if 'नेपाल' in msg['content'] or 'nepal' in msg['content'].lower():
                        last_topic = 'Nepal'
                        break
                    if 'काठमाडौं' in msg['content'] or 'kathmandu' in msg['content'].lower():
                        last_topic = 'Kathmandu'
                        break
            
            if last_topic:
                # REWRITE THE QUESTION
                original = request.message.strip()
                actual_question = f"{original} of {last_topic}"
                
                logger.error(f"🔴🔴🔴 QUESTION REWRITTEN")
                logger.error(f"   Original: '{request.message}'")
                logger.error(f"   Rewritten: '{actual_question}'")
                logger.error(f"   Topic: {last_topic}")
                logger.error(f"   → LLM will see the REWRITTEN version")
        
        # INTELLIGENT MODEL SELECTION
        # Choose best model based on question complexity and language
        model_config = model_router.select_best_model(
            question=actual_question,
            language=getattr(request, 'language_code', 'en-US'),
            context=context_info,
            user_preference=request.model
        )
        
        selected_provider = model_config['provider']
        selected_model = model_config['model']
        
        logger.info(f"🤖 Selected: {selected_provider}/{selected_model}")
        logger.info(f"   → Reason: Context={context_info.get('intent')}, Follow-up={context_info.get('is_followup')}")
        
        # AUTO TOOL CALLING (Like Perplexity)
        # Automatically search web, get weather, etc. based on question
        suggested_tools = auto_tool_caller.analyze_and_suggest_tools(
            question=actual_question,
            context=context_info,
            conversation_history=history_dicts
        )
        
        # Pre-execute tools if auto-triggered
        tool_results = []
        if suggested_tools:
            logger.info(f"🔧 AUTO-TRIGGERING {len(suggested_tools)} tools (Perplexity-style)")
            for tool_spec in suggested_tools:
                try:
                    result = await tool_manager.execute_tool(
                        tool_name=tool_spec['tool'],
                        arguments={**tool_spec['arguments'], 'operation': tool_spec['operation']}
                    )
                    tool_results.append({
                        'tool': tool_spec['tool'],
                        'reason': tool_spec['reason'],
                        'result': result
                    })
                    logger.success(f"   ✓ {tool_spec['tool']}: {tool_spec['reason']}")
                except Exception as e:
                    logger.error(f"   ✗ {tool_spec['tool']} failed: {e}")
        
        # Track interaction start time for learning
        import time
        start_time = time.time()
        tools_used = []
        
        # Get project context if in project mode
        project_context = None
        if request.project_id:
            project = await memory_manager.get_project(request.project_id)
            if project:
                project_context = project.context
        
        # Prepare system prompt with language instruction
        system_prompt = request.system_prompt
        
        # If language-specific override is provided, use it
        if request.system_prompt_override:
            system_prompt = request.system_prompt_override
        elif request.language and request.language != "English":
            # Add language instruction to base system prompt
            base_prompt = request.system_prompt or SYSTEM_PROMPT
            system_prompt = f"{base_prompt}\n\nIMPORTANT: You MUST respond in {request.language} language only. Use {request.language} for all your responses."
        
        # Inject tool results into context (if any)
        tool_context = ""
        if tool_results:
            tool_context = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            tool_context += "📊 REAL-TIME INFORMATION RETRIEVED:\n"
            tool_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for tr in tool_results:
                tool_context += f"\n🔧 {tr['tool'].upper()}: {tr['reason']}\n"
                tool_context += f"Result: {str(tr['result'])[:500]}...\n"
            tool_context += "\nUse this real-time information to answer the user's question.\n"
            tool_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Stream response from LLM
        full_response = ""
        tool_calls = []
        
        # Send tool results as first chunk if available
        if tool_results:
            for tr in tool_results:
                stream_chunk = StreamChunk(
                    type="tool_result",
                    data={
                        "tool": tr['tool'],
                        "result": tr['result'],
                        "reason": tr['reason']
                    }
                )
                yield f"data: {stream_chunk.model_dump_json()}\n\n"
        
        # Enhance system prompt with tool results
        enhanced_system_prompt = system_prompt + tool_context if tool_context else system_prompt
        
        async for chunk in llm_engine.stream_chat(
            message=actual_question,  # RESOLVED: Vague questions rewritten with context
            history=history,
            provider=selected_provider,  # INTELLIGENT: Auto-selected based on question
            model=selected_model,  # INTELLIGENT: Auto-selected for best results
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=enhanced_system_prompt,  # WITH TOOL RESULTS
            project_context=project_context,
            language=getattr(request, 'language_code', 'en-US')
        ):
            chunk_type = chunk.get("type")
            
            if chunk_type == "token":
                # Stream token to client
                content = chunk.get("content", "")
                full_response += content
                
                stream_chunk = StreamChunk(type="token", content=content)
                yield f"data: {stream_chunk.model_dump_json()}\n\n"
            
            elif chunk_type == "tool_call":
                # Handle tool call
                tool_data = chunk.get("data", {})
                tool_calls.append(tool_data)
                
                # Send tool call notification
                stream_chunk = StreamChunk(type="tool_call", data=tool_data)
                yield f"data: {stream_chunk.model_dump_json()}\n\n"
                
                # Execute tool
                logger.info(f"Executing tool: {tool_data.get('name')}")
                tool_result = await tool_manager.execute_tool(
                    tool_name=tool_data.get("name"),
                    arguments=tool_data.get("arguments", {})
                )
                
                # Send tool result
                stream_chunk = StreamChunk(
                    type="tool_result",
                    data={
                        "tool": tool_data.get("name"),
                        "result": tool_result
                    }
                )
                yield f"data: {stream_chunk.model_dump_json()}\n\n"
                
                # Add tool result to context for continuation
                full_response += f"\n\n[Tool: {tool_data.get('name')}]\n{json.dumps(tool_result, indent=2)}\n"
            
            elif chunk_type == "error":
                # Handle error
                stream_chunk = StreamChunk(
                    type="error",
                    content=chunk.get("content", "An error occurred")
                )
                yield f"data: {stream_chunk.model_dump_json()}\n\n"
                break
        
        # Save assistant response
        if full_response:
            await memory_manager.add_message(
                conversation.id,
                role="assistant",
                content=full_response,
                tool_calls=tool_calls if tool_calls else None
            )
            
            # Add to semantic memory for future context retrieval
            try:
                if semantic_memory.initialized:
                    semantic_memory.add_to_semantic_memory(
                        conversation_id=conversation.id,
                        message=request.message,
                        role="user"
                    )
                    semantic_memory.add_to_semantic_memory(
                        conversation_id=conversation.id,
                        message=full_response,
                        role="assistant"
                    )
            except Exception as e:
                logger.debug(f"Semantic memory update skipped: {e}")
            
            # Add to LangChain memory (conversation buffer)
            try:
                if langchain_memory.initialized:
                    langchain_memory.add_exchange(
                        conversation_id=conversation.id,
                        user_message=request.message,
                        ai_message=full_response
                    )
            except Exception as e:
                logger.debug(f"LangChain memory update skipped: {e}")
        
        # Learn from this interaction (self-learning system)
        try:
            response_time = time.time() - start_time
            tools_used_names = [tc.get("name") for tc in tool_calls] if tool_calls else []
            tools_used_names.extend([tr['tool'] for tr in tool_results])
            
            learning_system.learn_from_interaction(
                user_message=request.message,
                ai_response=full_response,
                language=getattr(request, 'language_code', 'en-US'),
                tools_used=tools_used_names,
                response_time=response_time
            )
            logger.debug(f"📚 Learned from interaction (tools: {tools_used_names}, time: {response_time:.2f}s)")
        except Exception as e:
            logger.warning(f"Failed to learn from interaction: {e}")
        
        # Generate follow-up suggestions (Like ChatGPT)
        followups = []
        try:
            if context_info.get('current_topic'):
                followups = followup_generator.generate_followups(
                    last_response=full_response,
                    current_topic=context_info.get('current_topic'),
                    conversation_history=history_dicts
                )
                
                if followups:
                    logger.info(f"💡 Generated {len(followups)} follow-up suggestions")
        except Exception as e:
            logger.debug(f"Follow-up generation skipped: {e}")
        
        # Send follow-up suggestions
        if followups:
            stream_chunk = StreamChunk(
                type="followups",
                data={"suggestions": followups}
            )
            yield f"data: {stream_chunk.model_dump_json()}\n\n"
        
        # Send completion signal
        stream_chunk = StreamChunk(type="done")
        yield f"data: {stream_chunk.model_dump_json()}\n\n"
        
    except Exception as e:
        logger.error("Streaming error: {error}", error=str(e), exc_info=True)
        error_chunk = StreamChunk(
            type="error",
            content=f"Error: {str(e)}"
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response with SSE"""
    # CONVERSATION FLOW:
    # 1. If conversation_id is None → CREATE NEW conversation
    # 2. If conversation_id provided → CONTINUE existing conversation
    conversation = await memory_manager.get_or_create_conversation(
        conversation_id=request.conversation_id,
        project_id=request.project_id
    )
    
    is_new = request.conversation_id is None
    
    if is_new:
        logger.info(f"🆕 NEW CONVERSATION created: {conversation.id}")
    else:
        logger.info(f"💬 CONTINUING conversation: {conversation.id}")
        logger.info(f"   → Existing messages: {len(conversation.messages)}")
    
    logger.debug(f"   → Request had conversation_id: {request.conversation_id}")
    logger.debug(f"   → Using conversation_id: {conversation.id}")
    
    return StreamingResponse(
        stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Conversation-ID": conversation.id  # Return conversation ID to frontend
        }
    )


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """Non-streaming chat endpoint"""
    try:
        # Get or create conversation
        conversation = await memory_manager.get_or_create_conversation(
            conversation_id=request.conversation_id,
            project_id=request.project_id
        )
        
        # Add user message
        await memory_manager.add_message(
            conversation.id,
            role="user",
            content=request.message
        )
        
        # Get conversation history
        history = await memory_manager.get_conversation_history(conversation.id)
        
        # Get project context
        project_context = None
        if request.project_id:
            project = await memory_manager.get_project(request.project_id)
            if project:
                project_context = project.context
        
        # Prepare system prompt with language instruction
        system_prompt = request.system_prompt
        
        # If language-specific override is provided, use it
        if request.system_prompt_override:
            system_prompt = request.system_prompt_override
        elif request.language and request.language != "English":
            # Add language instruction to base system prompt
            base_prompt = request.system_prompt or SYSTEM_PROMPT
            system_prompt = f"{base_prompt}\n\nIMPORTANT: You MUST respond in {request.language} language only. Use {request.language} for all your responses."
        
        # Get response from LLM
        response = await llm_engine.chat(
            message=request.message,
            history=history,
            provider=request.provider or settings.default_provider,
            model=request.model or settings.default_model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=system_prompt,
            project_context=project_context
        )
        
        # Save assistant response
        await memory_manager.add_message(
            conversation.id,
            role="assistant",
            content=response["content"]
        )
        
        return ChatResponse(
            response=response["content"],
            conversation_id=conversation.id,
            model=response.get("model", request.model or settings.default_model),
            provider=request.provider or settings.default_provider,
            tokens_used=response.get("tokens_used")
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation by ID"""
    conversation = await memory_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation"""
    success = await memory_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}


@router.delete("/conversations")
async def delete_all_conversations():
    """Delete all conversations"""
    count = await memory_manager.delete_all_conversations()
    logger.info(f"Deleted all conversations: {count} total")
    return {"message": f"Successfully deleted {count} conversations", "count": count}


@router.put("/conversations/{conversation_id}/name")
async def rename_conversation(conversation_id: str, name: str):
    """Rename a conversation"""
    try:
        success = await memory_manager.rename_conversation(conversation_id, name)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        logger.info(f"Renamed conversation {conversation_id} to: {name}")
        return {"message": "Conversation renamed successfully", "name": name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error renaming conversation: {error}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/generate-name")
async def generate_conversation_name(conversation_id: str):
    """Auto-generate conversation name based on content"""
    try:
        name = await memory_manager.generate_conversation_name(conversation_id)
        if not name:
            raise HTTPException(status_code=404, detail="Conversation not found or empty")
        
        logger.info(f"Generated name for {conversation_id}: {name}")
        return {"name": name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating name: {error}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations(project_id: str = None, limit: int = 50):
    """List conversations"""
    conversations = await memory_manager.list_conversations(
        project_id=project_id,
        limit=limit
    )
    return conversations

