"""
ULTRA-SIMPLE Conversation System
Guarantees ONE conversation per session
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from pathlib import Path
from loguru import logger


class SimpleConversation:
    """
    Dead-simple conversation manager
    ONE active conversation at a time
    """
    
    def __init__(self):
        self.active_conversation_id = None
        self.messages = []  # All messages in current conversation
        self.data_dir = Path("../data/simple_chats")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def start_new_conversation(self) -> str:
        """Start a brand new conversation"""
        # Save old one if exists
        if self.active_conversation_id and self.messages:
            self._save()
        
        # Create new
        self.active_conversation_id = str(uuid.uuid4())
        self.messages = []
        
        logger.warning(f"🆕 NEW CONVERSATION STARTED: {self.active_conversation_id}")
        return self.active_conversation_id
    
    def get_or_create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """
        Get conversation ID - SIMPLE LOGIC:
        - If conversation_id provided AND matches active → Continue
        - Otherwise → Create new
        """
        if conversation_id and conversation_id == self.active_conversation_id:
            logger.info(f"✅ CONTINUING: {conversation_id} ({len(self.messages)} msgs)")
            return self.active_conversation_id
        
        if conversation_id and conversation_id != self.active_conversation_id:
            # Load from disk
            loaded = self._load(conversation_id)
            if loaded:
                logger.info(f"📂 LOADED: {conversation_id} ({len(self.messages)} msgs)")
                return self.active_conversation_id
        
        # Create new
        return self.start_new_conversation()
    
    def add_message(self, role: str, content: str):
        """Add message to active conversation"""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(msg)
        
        logger.warning(f"💾 MSG ADDED: [{role}] {content[:50]}...")
        logger.warning(f"   Total in conversation: {len(self.messages)}")
        
        # Auto-save every message
        self._save()
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get full conversation history"""
        return self.messages.copy()
    
    def _save(self):
        """Save to disk"""
        if not self.active_conversation_id:
            return
        
        file_path = self.data_dir / f"{self.active_conversation_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'id': self.active_conversation_id,
                'messages': self.messages,
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
    
    def _load(self, conversation_id: str) -> bool:
        """Load from disk"""
        file_path = self.data_dir / f"{conversation_id}.json"
        
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.active_conversation_id = data['id']
            self.messages = data['messages']
            return True
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return False


# Global instance - ONE conversation manager
simple_conversation = SimpleConversation()

