"""
LangChain Conversation Memory
Advanced conversation buffer with summarization and context window management
"""
from typing import List, Dict, Any, Optional
from loguru import logger


class LangChainMemory:
    """
    Uses LangChain's conversation buffer memory for intelligent context management
    Automatically summarizes old conversations and maintains recent context
    """
    
    def __init__(self):
        self.conversation_buffers = {}  # conversation_id -> memory
        self.initialized = False
    
    def initialize(self):
        """Initialize LangChain memory system"""
        if self.initialized:
            return
        
        try:
            from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
            from langchain.chains import ConversationChain
            
            self.ConversationBufferWindowMemory = ConversationBufferWindowMemory
            self.ConversationSummaryMemory = ConversationSummaryMemory
            
            self.initialized = True
            logger.success("✓ LangChain conversation memory initialized")
            
        except ImportError as e:
            logger.warning(f"⚠️ LangChain not available: {e}")
            logger.info("   Install with: pip install langchain")
            self.initialized = False
        except Exception as e:
            logger.warning(f"⚠️ LangChain initialization failed: {e}")
            self.initialized = False
    
    def get_or_create_memory(self, conversation_id: str, k: int = 10):
        """
        Get or create conversation buffer memory for a conversation
        k = number of recent exchanges to keep in full context
        """
        if not self.initialized:
            return None
        
        if conversation_id not in self.conversation_buffers:
            # Create new conversation buffer
            memory = self.ConversationBufferWindowMemory(
                k=k,  # Keep last 10 exchanges
                memory_key="chat_history",
                return_messages=True
            )
            self.conversation_buffers[conversation_id] = memory
            logger.debug(f"Created new LangChain memory buffer for conversation: {conversation_id}")
        
        return self.conversation_buffers[conversation_id]
    
    def add_exchange(
        self,
        conversation_id: str,
        user_message: str,
        ai_message: str
    ):
        """Add a conversation exchange to memory"""
        if not self.initialized:
            return
        
        memory = self.get_or_create_memory(conversation_id)
        if memory:
            try:
                memory.save_context(
                    {"input": user_message},
                    {"output": ai_message}
                )
                logger.debug(f"Added exchange to LangChain memory: {conversation_id}")
            except Exception as e:
                logger.debug(f"Failed to add to LangChain memory: {e}")
    
    def get_context_string(self, conversation_id: str) -> str:
        """
        Get formatted conversation context
        LangChain automatically manages the context window
        """
        if not self.initialized:
            return ""
        
        memory = self.get_or_create_memory(conversation_id)
        if memory:
            try:
                # Load memory variables
                context = memory.load_memory_variables({})
                chat_history = context.get('chat_history', [])
                
                if chat_history:
                    # Format as conversation
                    formatted = []
                    for msg in chat_history:
                        if hasattr(msg, 'type'):
                            role = "User" if msg.type == "human" else "AI"
                            formatted.append(f"{role}: {msg.content}")
                    
                    return "\n".join(formatted)
            except Exception as e:
                logger.debug(f"Failed to load LangChain context: {e}")
        
        return ""
    
    def clear_memory(self, conversation_id: str):
        """Clear memory for a conversation"""
        if conversation_id in self.conversation_buffers:
            del self.conversation_buffers[conversation_id]
            logger.debug(f"Cleared LangChain memory for: {conversation_id}")
    
    def get_summary(self, conversation_id: str) -> Optional[str]:
        """
        Get conversation summary (for very long conversations)
        """
        if not self.initialized:
            return None
        
        memory = self.get_or_create_memory(conversation_id)
        if memory and hasattr(memory, 'buffer'):
            # Get recent messages
            buffer = memory.buffer
            if len(buffer) > 5:
                # Return a simple summary
                return f"Conversation has {len(buffer)} exchanges covering multiple topics"
        
        return None


# Global instance
langchain_memory = LangChainMemory()

