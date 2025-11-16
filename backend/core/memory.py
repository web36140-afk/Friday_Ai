"""
Memory Manager - Conversation history and vector store
Supports persistent context and semantic search
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from models.schemas import Conversation, Message, Project
from config import settings

# Import Firestore storage if available
try:
    from core.firestore_storage import firestore_storage
    FIRESTORE_ENABLED = settings.use_firestore and firestore_storage and firestore_storage.initialized
except:
    FIRESTORE_ENABLED = False
    firestore_storage = None


class MemoryManager:
    """Manages conversations, projects, and vector memory"""
    
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.projects: Dict[str, Project] = {}
        self.vector_store = None
        self.embeddings = None
        self.initialized = False
        self.use_firestore = FIRESTORE_ENABLED
        self.firestore = firestore_storage if FIRESTORE_ENABLED else None
        
        if self.use_firestore:
            logger.info("🔥 Using Firestore for cloud storage")
        else:
            logger.info("💾 Using local file storage")
    
    async def initialize(self):
        """Initialize memory manager and vector store"""
        if self.initialized:
            return
        
        # Load existing conversations and projects
        await self._load_from_disk()
        
        # Initialize vector store if enabled
        if settings.enable_vector_memory:
            try:
                import chromadb
                from sentence_transformers import SentenceTransformer
                
                # Initialize ChromaDB
                self.vector_store = chromadb.PersistentClient(
                    path=settings.vector_db_path
                )
                
                # Get or create collection
                self.collection = self.vector_store.get_or_create_collection(
                    name="jarvis_memory",
                    metadata={"description": "JARVIS conversation memory"}
                )
                
                # Initialize embeddings model
                self.embeddings = SentenceTransformer(settings.embedding_model)
                
                logger.success("✓ Vector memory initialized")
            except Exception as e:
                logger.warning(f"Vector memory initialization failed: {e}")
        
        self.initialized = True
        logger.info("Memory manager initialized")
    
    async def _load_from_disk(self):
        """Load conversations and projects from disk"""
        # Load conversations
        conv_dir = Path(settings.conversations_dir)
        if conv_dir.exists():
            for file_path in conv_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        conversation = Conversation(**data)
                        self.conversations[conversation.id] = conversation
                except Exception as e:
                    logger.warning(f"Failed to load conversation {file_path}: {e}")
        
        # Load projects
        proj_dir = Path(settings.projects_dir)
        if proj_dir.exists():
            for file_path in proj_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        project = Project(**data)
                        self.projects[project.id] = project
                except Exception as e:
                    logger.warning(f"Failed to load project {file_path}: {e}")
        
        logger.info(f"Loaded {len(self.conversations)} conversations and {len(self.projects)} projects")
    
    async def _save_conversation(self, conversation: Conversation):
        """Save conversation to storage (Firestore or local disk)"""
        # Save to Firestore if enabled
        if self.use_firestore and self.firestore:
            await self.firestore.save_conversation(conversation)
        
        # Always save locally as backup
        conv_dir = Path(settings.conversations_dir)
        conv_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = conv_dir / f"{conversation.id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation.model_dump(), f, indent=2, default=str)
    
    async def _save_project(self, project: Project):
        """Save project to storage (Firestore or local disk)"""
        # Save to Firestore if enabled
        if self.use_firestore and self.firestore:
            await self.firestore.save_project(project)
        
        # Always save locally as backup
        proj_dir = Path(settings.projects_dir)
        proj_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = proj_dir / f"{project.id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project.model_dump(), f, indent=2, default=str)
    
    async def get_or_create_conversation(
        self,
        conversation_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Conversation:
        """Get existing conversation or create new one - FIXED VERSION"""
        
        # If conversation_id provided, try to get it first
        if conversation_id:
            logger.info(f"🔍 Looking for conversation: {conversation_id}")
            logger.info(f"   In memory: {conversation_id in self.conversations}")
            
            # Check memory first
            if conversation_id in self.conversations:
                logger.info(f"✅ Found in memory - returning existing conversation")
                logger.info(f"   Messages: {len(self.conversations[conversation_id].messages)}")
                return self.conversations[conversation_id]
            
            # Try to load from disk if not in memory
            logger.warning(f"⚠️ Not in memory - trying to load from disk")
            loaded_conv = await self.storage.load_conversation(conversation_id)
            if loaded_conv:
                logger.info(f"✅ Loaded from disk!")
                self.conversations[conversation_id] = loaded_conv
                return loaded_conv
            else:
                logger.error(f"❌ Conversation {conversation_id} not found on disk either!")
                logger.error(f"   Creating NEW conversation instead (this might be the bug!)")
        
        # Create new conversation
        new_id = conversation_id or str(uuid.uuid4())
        
        logger.warning(f"🆕 CREATING NEW CONVERSATION")
        logger.warning(f"   New ID: {new_id}")
        logger.warning(f"   Requested ID was: {conversation_id}")
        logger.warning(f"   Project ID: {project_id}")
        
        conversation = Conversation(
            id=new_id,
            project_id=project_id,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.conversations[new_id] = conversation
        await self._save_conversation(conversation)
        
        # Link to project if specified
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
            if new_id not in project.conversation_ids:
                project.conversation_ids.append(new_id)
                await self._save_project(project)
        
        logger.info(f"✅ Created new conversation: {new_id}")
        return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ):
        """Add message to conversation WITH DEBUGGING"""
        if conversation_id not in self.conversations:
            logger.error(f"❌ Cannot add message - conversation {conversation_id} NOT FOUND in memory!")
            logger.error(f"   Available conversations: {list(self.conversations.keys())}")
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        
        message = Message(
            role=role,
            content=content,
            tool_calls=tool_calls,
            timestamp=datetime.now()
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # Save to disk
        if settings.auto_save_conversations:
            await self._save_conversation(conversation)
        
        # Add to vector store for semantic search
        if self.vector_store and role in ["user", "assistant"]:
            await self._add_to_vector_store(conversation_id, message)
        
        # ENHANCED LOGGING
        logger.warning(f"💾 ✅ MESSAGE SAVED TO CONVERSATION")
        logger.warning(f"   Conversation ID: {conversation_id}")
        logger.warning(f"   Role: {role}")
        logger.warning(f"   Content: {content[:80]}")
        logger.warning(f"   Total messages in this conversation: {len(conversation.messages)}")
    
    async def _add_to_vector_store(self, conversation_id: str, message: Message):
        """Add message to vector store"""
        try:
            # Generate embedding
            embedding = self.embeddings.encode(message.content).tolist()
            
            # Add to ChromaDB
            self.collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                documents=[message.content],
                metadatas=[{
                    "conversation_id": conversation_id,
                    "role": message.role,
                    "timestamp": message.timestamp.isoformat()
                }]
            )
        except Exception as e:
            logger.warning(f"Failed to add to vector store: {e}")
    
    async def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search through conversation history"""
        if not self.vector_store:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.encode(query).tolist()
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            return results
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get conversation history"""
        if conversation_id not in self.conversations:
            return []
        
        messages = self.conversations[conversation_id].messages
        
        if limit:
            return messages[-limit:]
        
        return messages
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        if conversation_id not in self.conversations:
            return False
        
        # Remove from memory
        del self.conversations[conversation_id]
        
        # Delete file
        file_path = Path(settings.conversations_dir) / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"Deleted conversation: {conversation_id}")
        return True
    
    async def delete_all_conversations(self) -> int:
        """Delete all conversations"""
        count = len(self.conversations)
        
        # Delete all files
        conversations_path = Path(settings.conversations_dir)
        if conversations_path.exists():
            for file_path in conversations_path.glob("*.json"):
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
        
        # Clear memory
        self.conversations.clear()
        
        logger.info(f"Deleted all {count} conversations")
        return count
    
    async def rename_conversation(self, conversation_id: str, name: str) -> bool:
        """Rename a conversation"""
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        conversation.name = name
        conversation.updated_at = datetime.now()
        
        # Save to disk
        await self._save_conversation(conversation)
        
        logger.info(f"Renamed conversation {conversation_id} to: {name}")
        return True
    
    async def generate_conversation_name(self, conversation_id: str) -> Optional[str]:
        """
        Auto-generate smart conversation name from actual content
        Works for English, Hindi, and Nepali
        """
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        
        # If already has a custom name (user renamed it), keep it
        if conversation.name and not conversation.name.startswith("Chat") and not conversation.name.startswith("New"):
            logger.info(f"Keeping custom name: {conversation.name}")
            return conversation.name
        
        # Get first user message
        user_messages = [msg for msg in conversation.messages if msg.role == "user"]
        if not user_messages:
            return "New Chat"
        
        first_message = user_messages[0].content.strip()
        
        # Smart name extraction - different for each language
        name = self._extract_smart_name(first_message)
        
        # Update conversation
        conversation.name = name
        conversation.updated_at = datetime.now()
        await self._save_conversation(conversation)
        
        logger.info(f"Auto-generated name: '{name}' from message: '{first_message[:50]}...'")
        return name
    
    def _extract_smart_name(self, message: str) -> str:
        """Extract a smart, meaningful name from message content"""
        # Truncate very long messages
        if len(message) > 100:
            message = message[:100]
        
        # Check if it's Hindi (Devanagari script)
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in message)
        
        if has_devanagari:
            # For Hindi/Nepali - just use first meaningful phrase
            # Remove common question words
            words = message.split()
            # Skip common starting words
            skip_words = {'क्या', 'कैसे', 'कब', 'कहाँ', 'क्यों', 'मुझे', 'मेरा', 'के', 'को', 'से', 'में'}
            meaningful = [w for w in words if w not in skip_words]
            
            # Take first 3-4 words for name
            name_words = meaningful[:4] if len(meaningful) >= 4 else words[:4]
            return ' '.join(name_words)
        else:
            # For English - filter stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 
                'of', 'with', 'is', 'are', 'was', 'were', 'be', 'i', 'you', 
                'what', 'which', 'who', 'when', 'where', 'why', 'how', 
                'my', 'your', 'please', 'tell', 'me', 'about', 'can'
            }
            
            words = message.split()
            meaningful_words = []
            
            for word in words:
                cleaned = word.strip('.,!?;:()[]{}"\'-').lower()
                if cleaned and len(cleaned) > 2 and cleaned not in stop_words:
                    meaningful_words.append(word.strip('.,!?;:()[]{}"\'-'))
                
                if len(meaningful_words) >= 4:
                    break
            
            # If not enough meaningful words, take first 5 words
            if len(meaningful_words) < 2:
                meaningful_words = [w.strip('.,!?;:()[]{}"\'-') for w in words[:5]]
            
            name = ' '.join(meaningful_words[:4])
            return name[0].upper() + name[1:] if name else "New Chat"
    
    async def list_conversations(
        self,
        project_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Conversation]:
        """List conversations"""
        conversations = list(self.conversations.values())
        
        if project_id:
            conversations = [c for c in conversations if c.project_id == project_id]
        
        # Sort by updated_at
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        
        return conversations[:limit]
    
    # ============================================
    # Project Management
    # ============================================
    
    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Project:
        """Create new project"""
        project_id = str(uuid.uuid4())
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            context=initial_context or {},
            conversation_ids=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.projects[project_id] = project
        await self._save_project(project)
        
        logger.info(f"Created project: {name} ({project_id})")
        return project
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        return self.projects.get(project_id)
    
    async def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Project]:
        """Update project"""
        if project_id not in self.projects:
            return None
        
        project = self.projects[project_id]
        
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if context is not None:
            project.context.update(context)
        if metadata is not None:
            project.metadata.update(metadata)
        
        project.updated_at = datetime.now()
        
        await self._save_project(project)
        logger.info(f"Updated project: {project_id}")
        
        return project
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete project"""
        if project_id not in self.projects:
            return False
        
        # Remove from memory
        del self.projects[project_id]
        
        # Delete file
        file_path = Path(settings.projects_dir) / f"{project_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"Deleted project: {project_id}")
        return True
    
    async def list_projects(self, limit: int = 100) -> List[Project]:
        """List all projects"""
        projects = list(self.projects.values())
        projects.sort(key=lambda p: p.updated_at, reverse=True)
        return projects[:limit]
    
    async def save_all(self):
        """Save all conversations and projects"""
        for conversation in self.conversations.values():
            await self._save_conversation(conversation)
        
        for project in self.projects.values():
            await self._save_project(project)
        
        logger.info("Saved all conversations and projects")


# Global instance
memory_manager = MemoryManager()

