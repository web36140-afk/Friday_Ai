"""
Simple Conversation Store - Single Source of Truth
Replaces all the complex memory systems
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class ConversationStore:
    """
    Dead-simple conversation storage
    Just a dictionary in memory + JSON files on disk
    """
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
        self.data_dir = Path("../data/chats")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.load_all()
    
    def load_all(self):
        """Load all conversations from disk on startup"""
        try:
            count = 0
            for file_path in self.data_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.conversations[data['id']] = data['messages']
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to load {file_path.name}: {e}")
            
            logger.success(f"✓ Loaded {count} conversations from disk")
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
    
    def save(self, conversation_id: str):
        """Save conversation to disk"""
        if conversation_id not in self.conversations:
            return
        
        try:
            file_path = self.data_dir / f"{conversation_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'id': conversation_id,
                    'messages': self.conversations[conversation_id],
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Save failed: {e}")
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """Add message to conversation"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Auto-save
        self.save(conversation_id)
        
        logger.info(f"💾 Added {role} message to {conversation_id}")
        logger.info(f"   Total messages: {len(self.conversations[conversation_id])}")
    
    def get_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages in conversation"""
        return self.conversations.get(conversation_id, [])
    
    def exists(self, conversation_id: str) -> bool:
        """Check if conversation exists"""
        return conversation_id in self.conversations
    
    def delete(self, conversation_id: str):
        """Delete conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        
        file_path = self.data_dir / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
    
    def get_all_ids(self) -> List[str]:
        """Get all conversation IDs"""
        return list(self.conversations.keys())


# Global instance
conversation_store = ConversationStore()

