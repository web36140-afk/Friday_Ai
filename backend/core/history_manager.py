"""
Smart History Manager
Prevents token limit errors by intelligently managing conversation history
"""

from typing import List, Dict, Any
from loguru import logger


class HistoryManager:
    """
    Manages conversation history to prevent token limit errors
    """
    
    # Provider token limits (conservative estimates)
    PROVIDER_LIMITS = {
        "groq": 6000,      # Groq: 8k tokens (use 6k for safety)
        "gemini": 24000,   # Gemini: 32k tokens (use 24k for safety)
        "openai": 14000,   # OpenAI: 16k tokens (use 14k for safety)
        "claude": 90000    # Claude: 100k tokens (use 90k for safety)
    }
    
    # History message limits
    MAX_MESSAGES = {
        "groq": 15,    # ~7-8 exchanges
        "gemini": 30,  # ~15 exchanges (better multilingual)
        "openai": 20,  # ~10 exchanges
        "claude": 40   # ~20 exchanges
    }
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count
        Rule of thumb: 1 token ≈ 4 characters for English
        For non-English (Hindi/Nepali): 1 token ≈ 2-3 characters
        """
        # Check if text contains non-ASCII (Hindi/Nepali)
        has_unicode = any(ord(char) > 127 for char in text)
        
        if has_unicode:
            # Non-English text: more tokens per character
            return len(text) // 2
        else:
            # English text
            return len(text) // 4
    
    @staticmethod
    def calculate_message_tokens(messages: List[Dict[str, str]]) -> int:
        """Calculate total tokens in messages"""
        total = 0
        for msg in messages:
            total += HistoryManager.estimate_tokens(msg.get("content", ""))
            total += 4  # Role, name, formatting tokens
        return total
    
    @staticmethod
    def truncate_history(
        history: List[Dict[str, str]],
        provider: str = "groq",
        system_prompt_tokens: int = 500,
        current_message_tokens: int = 100
    ) -> List[Dict[str, str]]:
        """
        Truncate history to fit within token limits
        
        Strategy:
        1. Keep most recent messages (they're most relevant)
        2. Ensure we stay under provider's token limit
        3. Always keep at least 4 messages (2 exchanges) for context
        """
        
        # Get limits for provider
        token_limit = HistoryManager.PROVIDER_LIMITS.get(provider, 6000)
        max_messages = HistoryManager.MAX_MESSAGES.get(provider, 15)
        
        # Calculate available tokens for history
        available_tokens = token_limit - system_prompt_tokens - current_message_tokens - 200  # 200 buffer
        
        # Start with max messages limit
        truncated = history[-max_messages:]
        
        # Check token count
        history_tokens = HistoryManager.calculate_message_tokens(truncated)
        
        # If still over limit, reduce further
        while history_tokens > available_tokens and len(truncated) > 4:
            # Remove oldest message
            truncated = truncated[1:]
            history_tokens = HistoryManager.calculate_message_tokens(truncated)
        
        # Log truncation
        if len(truncated) < len(history):
            removed = len(history) - len(truncated)
            logger.info(f"📊 History truncated: {len(history)} → {len(truncated)} messages (removed {removed})")
            logger.info(f"   Tokens: {history_tokens} / {available_tokens} available")
        
        return truncated
    
    @staticmethod
    def summarize_old_messages(messages: List[Dict[str, str]], keep_recent: int = 6) -> str:
        """
        Create a summary of old messages (for future enhancement)
        Keeps recent messages, summarizes older ones
        """
        if len(messages) <= keep_recent:
            return ""
        
        old_messages = messages[:-keep_recent]
        
        # Extract key topics
        topics = []
        for msg in old_messages:
            if msg["role"] == "user":
                # Extract first few words as topic
                content = msg["content"][:100]
                topics.append(content)
        
        if topics:
            summary = "Earlier discussion: " + " → ".join(topics[:3])
            return summary
        
        return ""
    
    @staticmethod
    def get_safe_history(
        history: List[Dict[str, str]],
        provider: str,
        system_prompt: str,
        current_message: str
    ) -> List[Dict[str, str]]:
        """
        Get safe history that won't cause token limit errors
        
        This is the main method to use
        """
        # Calculate token counts
        system_tokens = HistoryManager.estimate_tokens(system_prompt)
        current_tokens = HistoryManager.estimate_tokens(current_message)
        
        # Truncate history
        safe_history = HistoryManager.truncate_history(
            history=history,
            provider=provider,
            system_prompt_tokens=system_tokens,
            current_message_tokens=current_tokens
        )
        
        return safe_history


# Global instance
history_manager = HistoryManager()

