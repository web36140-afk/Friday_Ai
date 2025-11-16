"""
Firestore Storage Adapter for JARVIS
Provides cloud-based storage for conversations and projects
"""
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud.firestore_v1 import FieldFilter
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logger.warning("Firebase libraries not installed. Firestore support disabled.")

from config import settings
from models.schemas import Conversation, Project, Message


class FirestoreStorage:
    """Firestore cloud storage adapter"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        
        if not FIRESTORE_AVAILABLE:
            logger.warning("Firestore not available - install firebase-admin")
            return
        
        if settings.use_firestore:
            self._initialize_firestore()
    
    def _initialize_firestore(self):
        """Initialize Firestore connection"""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self.db = firestore.client()
                self.initialized = True
                logger.info("✅ Firestore already initialized")
                return
            
            # Initialize from JSON string (for Railway/Render)
            if settings.firebase_credentials_json:
                cred_dict = json.loads(settings.firebase_credentials_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firestore initialized from JSON credentials")
            
            # Initialize from file
            elif settings.firebase_credentials_path:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firestore initialized from credentials file")
            
            # Initialize with project ID only (uses default credentials)
            elif settings.firebase_project_id:
                firebase_admin.initialize_app(options={
                    'projectId': settings.firebase_project_id
                })
                logger.info("✅ Firestore initialized with project ID")
            
            else:
                logger.error("❌ No Firebase credentials provided")
                return
            
            self.db = firestore.client()
            self.initialized = True
            
            logger.info("🔥 Firestore connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            self.initialized = False
    
    # ============================================
    # Conversation Operations
    # ============================================
    
    async def save_conversation(self, conversation: Conversation) -> bool:
        """Save conversation to Firestore"""
        if not self.initialized:
            return False
        
        try:
            # Convert to dict
            conv_dict = {
                'id': conversation.id,
                'name': conversation.name,
                'project_id': conversation.project_id,
                'messages': [
                    {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat() if isinstance(msg.timestamp, datetime) else msg.timestamp
                    }
                    for msg in conversation.messages
                ],
                'created_at': conversation.created_at.isoformat() if isinstance(conversation.created_at, datetime) else conversation.created_at,
                'updated_at': conversation.updated_at.isoformat() if isinstance(conversation.updated_at, datetime) else conversation.updated_at
            }
            
            # Save to Firestore
            self.db.collection('conversations').document(conversation.id).set(conv_dict)
            
            logger.debug(f"Saved conversation to Firestore: {conversation.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation to Firestore: {e}")
            return False
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation from Firestore"""
        if not self.initialized:
            return None
        
        try:
            doc = self.db.collection('conversations').document(conversation_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Convert back to Conversation object
            messages = [
                Message(
                    role=msg['role'],
                    content=msg['content'],
                    timestamp=datetime.fromisoformat(msg['timestamp']) if isinstance(msg['timestamp'], str) else msg['timestamp']
                )
                for msg in data.get('messages', [])
            ]
            
            return Conversation(
                id=data['id'],
                name=data.get('name'),
                project_id=data.get('project_id'),
                messages=messages,
                created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
                updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation from Firestore: {e}")
            return None
    
    async def list_conversations(self, limit: int = 50) -> List[Conversation]:
        """List all conversations from Firestore"""
        if not self.initialized:
            return []
        
        try:
            # Query conversations, ordered by updated_at
            docs = (
                self.db.collection('conversations')
                .order_by('updated_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            
            conversations = []
            for doc in docs:
                data = doc.to_dict()
                
                messages = [
                    Message(
                        role=msg['role'],
                        content=msg['content'],
                        timestamp=datetime.fromisoformat(msg['timestamp']) if isinstance(msg['timestamp'], str) else msg['timestamp']
                    )
                    for msg in data.get('messages', [])
                ]
                
                conversations.append(Conversation(
                    id=data['id'],
                    name=data.get('name'),
                    project_id=data.get('project_id'),
                    messages=messages,
                    created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
                    updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
                ))
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error listing conversations from Firestore: {e}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from Firestore"""
        if not self.initialized:
            return False
        
        try:
            self.db.collection('conversations').document(conversation_id).delete()
            logger.info(f"Deleted conversation from Firestore: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation from Firestore: {e}")
            return False
    
    async def delete_all_conversations(self) -> int:
        """Delete all conversations from Firestore"""
        if not self.initialized:
            return 0
        
        try:
            batch = self.db.batch()
            docs = self.db.collection('conversations').stream()
            
            count = 0
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
            
            batch.commit()
            logger.info(f"Deleted {count} conversations from Firestore")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting all conversations from Firestore: {e}")
            return 0
    
    # ============================================
    # Project Operations
    # ============================================
    
    async def save_project(self, project: Project) -> bool:
        """Save project to Firestore"""
        if not self.initialized:
            return False
        
        try:
            project_dict = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'context': project.context,
                'files': project.files,
                'created_at': project.created_at.isoformat() if isinstance(project.created_at, datetime) else project.created_at,
                'updated_at': project.updated_at.isoformat() if isinstance(project.updated_at, datetime) else project.updated_at
            }
            
            self.db.collection('projects').document(project.id).set(project_dict)
            logger.debug(f"Saved project to Firestore: {project.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project to Firestore: {e}")
            return False
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project from Firestore"""
        if not self.initialized:
            return None
        
        try:
            doc = self.db.collection('projects').document(project_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            return Project(
                id=data['id'],
                name=data['name'],
                description=data.get('description', ''),
                context=data.get('context', ''),
                files=data.get('files', []),
                created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
                updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
            )
            
        except Exception as e:
            logger.error(f"Error getting project from Firestore: {e}")
            return None
    
    async def list_projects(self, limit: int = 50) -> List[Project]:
        """List all projects from Firestore"""
        if not self.initialized:
            return []
        
        try:
            docs = (
                self.db.collection('projects')
                .order_by('updated_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            
            projects = []
            for doc in docs:
                data = doc.to_dict()
                
                projects.append(Project(
                    id=data['id'],
                    name=data['name'],
                    description=data.get('description', ''),
                    context=data.get('context', ''),
                    files=data.get('files', []),
                    created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
                    updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data['updated_at'], str) else data['updated_at']
                ))
            
            return projects
            
        except Exception as e:
            logger.error(f"Error listing projects from Firestore: {e}")
            return []
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete project from Firestore"""
        if not self.initialized:
            return False
        
        try:
            self.db.collection('projects').document(project_id).delete()
            logger.info(f"Deleted project from Firestore: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting project from Firestore: {e}")
            return False


# Global instance
firestore_storage = FirestoreStorage() if settings.use_firestore else None

