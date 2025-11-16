"""
LLM Engine - Multi-Provider Support
JARVIS AI Assistant - Groq (English) + Gemini (Hindi/Nepali)
"""
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from loguru import logger

from config import settings, SYSTEM_PROMPT, PROJECT_MODE_PROMPT_ADDITION, PROVIDERS
from models.schemas import Message
from core.context_tracker import context_tracker
from core.smart_nlp import smart_nlp
from core.reasoning_engine import reasoning_engine
from core.semantic_memory import semantic_memory
from core.chatgpt_context import build_chatgpt_style_messages
from core.conversation_rag import conversation_rag
from core.history_manager import history_manager


class LLMEngine:
    """Multi-provider LLM interface with language-specific routing"""
    
    def __init__(self):
        self.providers = {}
        self.initialized = False
        self.language_provider_map = {}
    
    async def initialize(self):
        """Initialize all available providers"""
        if self.initialized:
            return
        
        # Initialize Groq (for English - best performance)
        if settings.groq_api_key:
            try:
                from groq import AsyncGroq
                self.providers["groq"] = AsyncGroq(api_key=settings.groq_api_key)
                logger.success("✓ Groq AI initialized (English)")
            except Exception as e:
                logger.error("Groq initialization failed: {error}", error=str(e))
        
        # Initialize Google Gemini (for Hindi & Nepali - better multilingual)
        if settings.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self.providers["gemini"] = genai
                logger.success("✓ Google Gemini initialized (Hindi, Nepali)")
            except Exception as e:
                logger.warning("Gemini initialization failed: {error}", error=str(e))
        
        # Parse language provider mapping
        try:
            self.language_provider_map = json.loads(settings.language_provider_map)
        except:
            self.language_provider_map = {
                "en-US": "groq",
                "ne-NP": "gemini",
                "hi-IN": "gemini"
            }
        
        if not self.providers:
            raise Exception("No LLM providers available. Please set GROQ_API_KEY or GOOGLE_API_KEY in .env")
        
        self.initialized = True
        logger.info(f"LLM Engine initialized with providers: {list(self.providers.keys())}")
    
    def _build_system_prompt(
        self,
        custom_prompt: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None,
        language: str = "en-US"
    ) -> str:
        """Build system prompt with project context and language"""
        # Use language-specific prompt if available
        from config import LANGUAGE_ENHANCED_PROMPTS
        
        if language in LANGUAGE_ENHANCED_PROMPTS and not custom_prompt:
            base_prompt = LANGUAGE_ENHANCED_PROMPTS[language]
            logger.info(f"🌍 Using {language} enhanced prompt")
        else:
            base_prompt = custom_prompt or SYSTEM_PROMPT
        
        if project_context:
            project_addition = PROJECT_MODE_PROMPT_ADDITION.format(
                project_name=project_context.get("name", "Unknown"),
                project_context=json.dumps(project_context.get("context", {}), indent=2),
                recent_messages=project_context.get("recent_summary", "")
            )
            base_prompt = f"{base_prompt}\n\n{project_addition}"
        
        return base_prompt
    
    def _format_messages(
        self,
        message: str,
        history: List[Message],
        system_prompt: str,
        provider: str = "groq"
    ) -> List[Dict[str, str]]:
        """
        Format messages with SMART HISTORY LIMITING
        Prevents token limit errors while maintaining context
        """
        # Convert history to dict format
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in history
            if msg.role in ["user", "assistant"]
        ]
        
        # Use history manager to get safe history
        safe_history = history_manager.get_safe_history(
            history=history_dicts,
            provider=provider,
            system_prompt=system_prompt,
            current_message=message
        )
        
        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add safe history
        messages.extend(safe_history)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Calculate tokens for logging
        total_tokens = history_manager.calculate_message_tokens(messages)
        
        logger.info(f"📝 Messages: {len(messages)} | History: {len(safe_history)} | Tokens: ~{total_tokens}")
        
        return messages
    
    def _format_messages_OLD_COMPLEX(
        self,
        message: str,
        history: List[Message],
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """
        OLD COMPLEX METHOD - Kept as backup
        """
        # Convert history to dict format for context extraction (LIMITED)
        MAX_HISTORY_FOR_CONTEXT = 20  # Limit for complex processing
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in history[-MAX_HISTORY_FOR_CONTEXT:]
            if msg.role in ["user", "assistant"]
        ]
        
        # AUTOMATIC CONTEXT EXTRACTION (No manual training needed!)
        context_info = context_tracker.extract_context(history_dicts)
        context_prompt = context_tracker.build_context_prompt(context_info)
        
        # SEMANTIC CONTEXT RETRIEVAL (Like ChatGPT)
        # Use vector similarity to find relevant context
        semantic_context = ""
        if semantic_memory.initialized and len(history_dicts) >= 2:
            try:
                # Find semantically relevant previous messages
                # This helps with long conversations where the topic was mentioned earlier
                relevant_context = semantic_memory.find_relevant_context(
                    query=message,
                    conversation_id="temp",  # Will be replaced with actual conversation_id
                    top_k=2
                )
                
                if relevant_context:
                    semantic_context = "\n🔮 SEMANTICALLY RELEVANT CONTEXT (from earlier in conversation):\n"
                    for ctx in relevant_context:
                        semantic_context += f"   → {ctx['content'][:100]}...\n"
                    semantic_context += "\n"
                    logger.info(f"🔮 Retrieved {len(relevant_context)} semantically relevant messages")
            except Exception as e:
                logger.debug(f"Semantic context retrieval skipped: {e}")
        
        # Generate conversation summary
        conversation_summary = ""
        if semantic_memory.initialized:
            try:
                summary = semantic_memory.generate_context_summary(history_dicts)
                if summary:
                    conversation_summary = f"\n📝 CONVERSATION SUMMARY: {summary}\n"
            except Exception as e:
                logger.debug(f"Summary generation skipped: {e}")
        
        # CHATGPT-STYLE CONTEXT EXTRACTION
        nlp_insights = ""
        conversation_context = ""
        
        if history_dicts and len(history_dicts) >= 2:
            try:
                # Get last few exchanges
                last_user_msg = [m for m in history_dicts if m['role'] == 'user'][-1]['content']
                
                # Extract what we were JUST talking about
                previous_messages = history_dicts[-4:]  # Last 2 exchanges
                topics_discussed = []
                
                for msg in previous_messages:
                    if msg['role'] == 'user':
                        # Extract key topics from user messages
                        content = msg['content'].lower()
                        # Look for proper nouns and key subjects
                        import re
                        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', msg['content'])
                        topics_discussed.extend(capitalized)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_topics = []
                for topic in topics_discussed:
                    if topic.lower() not in seen:
                        seen.add(topic.lower())
                        unique_topics.append(topic)
                
                if unique_topics:
                    recent_topic = unique_topics[-1]  # Most recent topic
                    conversation_context = f"""
╔═══════════════════════════════════════════════════════════╗
║  🎯 CRITICAL: CONVERSATION CONTEXT (MANDATORY TO USE)    ║
╚═══════════════════════════════════════════════════════════╝

CURRENT TOPIC: {recent_topic}

PREVIOUS MESSAGES SUMMARY:
"""
                    for msg in previous_messages[-2:]:
                        role_icon = "👤" if msg['role'] == 'user' else "🤖"
                        conversation_context += f"{role_icon} {msg['content'][:100]}...\n"
                    
                    conversation_context += f"""
⚠️ IMPORTANT INSTRUCTIONS:
1. The user is CONTINUING the conversation about {recent_topic}
2. If the current question is vague (like a single word), it MUST relate to {recent_topic}
3. DO NOT ask "which {recent_topic}" - the context is already clear
4. Example: If user asks "mayor?", answer about the mayor OF {recent_topic}

Current Question: "{last_user_msg}"
↓
If vague, interpret as: [something related to {recent_topic}]
"""
                
                # Add NLP insights
                entities = smart_nlp.extract_named_entities(last_user_msg)
                if entities:
                    entity_texts = [e['text'] for e in entities[:3]]
                    nlp_insights += f"\n🔍 Entities: {', '.join(entity_texts)}"
                
                is_dependent = smart_nlp.is_context_dependent(last_user_msg)
                if is_dependent:
                    nlp_insights += f"\n⚠️ CONTEXT-DEPENDENT QUESTION - Must use history!"
                    nlp_insights += f"\n→ User is asking about: {unique_topics[-1] if unique_topics else 'previous topic'}"
                
            except Exception as e:
                logger.debug(f"Context extraction skipped: {e}")
        
        # REASONING ENHANCEMENT
        reasoning_prompt = reasoning_engine.enhance_with_reasoning(
            system_prompt, message, context_info
        )
        
        # Build CHATGPT-STYLE system prompt with FORCED context awareness
        enhanced_prompt = f"""{reasoning_prompt}

{semantic_context}

{conversation_summary}

{conversation_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 CHATGPT-STYLE CONTEXT SYSTEM (With Semantic Memory)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{context_prompt if context_prompt else "No previous context - this is the start of conversation."}

{nlp_insights}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 MANDATORY RULES (NEVER VIOLATE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 RULE #1: ALWAYS Use Conversation Context (MANDATORY)
   - Read the "CURRENT TOPIC" above
   - If user's question is vague/short, it's about the CURRENT TOPIC
   - NEVER EVER ask "which one?" when context is clear
   - NEVER give generic answers when context exists

🔴 RULE #2: Follow-up Questions (STRICTLY ENFORCE)
   - Single word questions = Related to previous topic
   - Example: Topic is "Kathmandu", user asks "mayor?" → Answer ONLY about Kathmandu's mayor
   - DO NOT explain what a mayor is in general - answer about THE SPECIFIC mayor

🔴 RULE #3: Natural Conversation Flow (CRITICAL)
   - Assume user is continuing the same subject unless they explicitly change topic
   - Don't lose context between messages
   - Think: "What was the last topic mentioned?" Then answer about THAT topic

🔴 VIOLATION EXAMPLES (NEVER DO THIS):
   ❌ User discusses "Kathmandu", asks "mayor?" → You explain "A mayor is a city official..." (WRONG!)
   ✅ User discusses "Kathmandu", asks "mayor?" → You say "The mayor of Kathmandu is..." (CORRECT!)
   
   ❌ User discusses "Python", asks "libraries?" → You explain "Libraries are collections of code..." (WRONG!)
   ✅ User discusses "Python", asks "libraries?" → You list "Python libraries include numpy, pandas..." (CORRECT!)

The conversation history below shows ALL previous messages. READ IT:
"""
        
        messages = [{"role": "system", "content": enhanced_prompt}]
        
        # Add conversation history (but NOT the last message yet)
        if len(history_dicts) > 0:
            messages.extend(history_dicts[:-1] if history_dicts[-1]['role'] == 'user' else history_dicts)
        
        # CHATGPT METHOD: For short/vague questions, MODIFY the message with context
        final_message = message
        
        if len(message.strip().split()) <= 3:  # Short question
            # Extract topic from recent conversation
            import re
            recent_topics = []
            for msg in history_dicts[-4:]:
                capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', msg.get('content', ''))
                recent_topics.extend(capitalized)
            
            if recent_topics:
                topic = recent_topics[-1]
                original_msg = message.strip().rstrip('?')
                
                # REWRITE the message to be explicit
                final_message = f"{original_msg} of {topic}? (Specifically about {topic}, not in general)"
                
                logger.warning(f"🔄 QUESTION REWRITTEN FOR CONTEXT")
                logger.warning(f"   Original: '{message}'")
                logger.warning(f"   Sent to LLM: '{final_message}'")
                logger.warning(f"   Context: {topic}")
        
        # Add the FINAL message (original or rewritten)
        messages.append({"role": "user", "content": final_message})
        
        logger.info(f"📝 Sending {len(messages)} messages with SMART CONTEXT")
        logger.info(f"   🎯 Topic: {context_info.get('current_topic', 'None')}")
        logger.info(f"   📍 Entities: {', '.join(context_info.get('entities', [])) or 'None'}")
        logger.debug(f"   → AI has automatic context awareness enabled")
        
        return messages
    
    def _get_provider_for_language(self, language: str) -> str:
        """Get the best provider for a given language"""
        provider = self.language_provider_map.get(language, "groq")
        
        # Fallback if preferred provider not available
        if provider not in self.providers:
            if "groq" in self.providers:
                provider = "groq"
            elif "gemini" in self.providers:
                provider = "gemini"
            else:
                provider = list(self.providers.keys())[0]
        
        return provider
    
    async def stream_chat(
        self,
        message: str,
        history: List[Message],
        provider: str = "groq",
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None,
        language: str = "en-US"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response using language-appropriate provider"""
        if not self.initialized:
            await self.initialize()
        
        # AUTO-SELECT provider based on language
        if language in ["hi-IN", "ne-NP"]:
            # Hindi & Nepali → Use Gemini (better multilingual support)
            provider = "gemini" if "gemini" in self.providers else "groq"
        else:
            # English → Use Groq (faster, excellent quality)
            provider = "groq" if "groq" in self.providers else "gemini"
        
        logger.info(f"🤖 Language: {language} → Provider: {provider.upper()}")
        
        if provider not in self.providers:
            yield {
                "type": "error",
                "content": f"No LLM provider available. Please configure API keys in .env file."
            }
            return
        
        try:
            # Build system prompt with language-specific instructions
            sys_prompt = self._build_system_prompt(system_prompt, project_context, language)
            
            # Format messages with provider info for smart limiting
            messages = self._format_messages(message, history, sys_prompt, provider)
            
            # Route to appropriate provider
            if provider == "groq":
                async for chunk in self._stream_groq(messages, model, temperature, max_tokens):
                    yield chunk
            elif provider == "gemini":
                async for chunk in self._stream_gemini(messages, model, temperature, max_tokens):
                    yield chunk
            else:
                yield {"type": "error", "content": f"Unknown provider: {provider}"}
        
        except Exception as e:
            logger.error("LLM streaming error: {error}", error=str(e), exc_info=True)
            yield {"type": "error", "content": str(e)}
    
    async def _stream_groq(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream Groq response"""
        client = self.providers["groq"]
        model = model or settings.default_model
        
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield {
                    "type": "token",
                    "content": chunk.choices[0].delta.content
                }
    
    async def _stream_gemini(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream Gemini response - excellent for Hindi & Nepali"""
        try:
            genai = self.providers["gemini"]
            model_name = model or settings.gemini_model or "gemini-2.5-flash"
            
            logger.info(f"🧠 Gemini: Using model {model_name}")
            
            # Convert messages to Gemini format
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
            conversation = [m for m in messages if m["role"] != "system"]
            
            logger.info(f"🧠 Gemini: Processing {len(conversation)} messages")
            
            # Create model instance with generation config
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens or 2048,
            }
            
            model_instance = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_msg if system_msg else None,
                generation_config=generation_config
            )
            
            # Convert to Gemini's conversation format
            gemini_messages = []
            for msg in conversation:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            logger.info(f"🧠 Gemini: Chat with {len(gemini_messages)} messages ({len(gemini_messages)-1} history + 1 current)")
            
            # Use start_chat with proper history for CONTEXT AWARENESS
            if len(gemini_messages) > 1:
                # Has history - use start_chat
                chat_history = gemini_messages[:-1]
                current_msg = gemini_messages[-1]["parts"][0]
                
                logger.info(f"🧠 Gemini: Starting chat with {len(chat_history)} history messages")
                chat = model_instance.start_chat(history=chat_history)
                
                logger.info(f"🧠 Gemini: Sending current message: {current_msg[:50]}...")
                response = chat.send_message(current_msg, stream=True)
            else:
                # First message - no history
                current_msg = gemini_messages[0]["parts"][0]
                logger.info(f"🧠 Gemini: First message (no history): {current_msg[:50]}...")
                response = model_instance.generate_content(current_msg, stream=True)
            
            logger.info(f"🧠 Gemini: Streaming response...")
            
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"🧠 Gemini chunk: {chunk.text[:30]}...")
                    yield {
                        "type": "token",
                        "content": chunk.text
                    }
                else:
                    logger.warning(f"🧠 Gemini chunk has no text: {chunk}")
                    
        except Exception as e:
            logger.error(f"🧠 Gemini ERROR: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Gemini API Error: {str(e)}"
            }
    
    async def chat(
        self,
        message: str,
        history: List[Message],
        provider: str = "groq",
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Non-streaming chat (collects full response)"""
        full_response = ""
        
        async for chunk in self.stream_chat(
            message, history, provider, model,
            temperature, max_tokens, system_prompt, project_context
        ):
            if chunk["type"] == "token":
                full_response += chunk["content"]
            elif chunk["type"] == "error":
                raise Exception(chunk["content"])
        
        return {
            "content": full_response,
            "model": model or settings.default_model,
            "provider": "groq"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of LLM providers"""
        health = {
            "status": "healthy",
            "providers": {}
        }
        
        for name, provider in self.providers.items():
            health["providers"][name] = {
                "available": True,
                "type": name
            }
        
        if not self.providers:
            health["status"] = "unhealthy"
            health["message"] = "No providers available"
        
        return health


# Global instance
llm_engine = LLMEngine()

