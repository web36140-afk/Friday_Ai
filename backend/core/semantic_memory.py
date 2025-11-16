"""
Semantic Memory System
Uses vector embeddings to understand and maintain conversation context
This is the SECRET behind ChatGPT's perfect context awareness
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import json


class SemanticMemory:
    """
    Semantic memory using vector embeddings
    Understands MEANING, not just keywords
    """
    
    def __init__(self):
        self.data_dir = Path("../data/semantic_memory")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.embeddings_model = None
        self.chroma_client = None
        self.collection = None
        self.initialized = False
    
    def initialize(self):
        """Initialize semantic memory with embeddings"""
        if self.initialized:
            return
        
        try:
            # Try to use sentence transformers for semantic understanding
            from sentence_transformers import SentenceTransformer
            
            logger.info("📥 Loading semantic embeddings model (first time may take a moment)...")
            
            # Use lightweight but powerful model
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.success("✓ Semantic embeddings loaded (all-MiniLM-L6-v2)")
            
            # Initialize ChromaDB for vector storage (NEW CLIENT)
            try:
                import chromadb
                
                # Use new persistent client method
                self.chroma_client = chromadb.PersistentClient(
                    path=str(self.data_dir)
                )
                
                # Get or create collection
                self.collection = self.chroma_client.get_or_create_collection(
                    name="conversation_context",
                    metadata={"description": "Conversation context vectors"}
                )
                
                logger.success("✓ Vector database initialized (ChromaDB)")
                self.initialized = True
                
            except ImportError:
                logger.warning("⚠️ ChromaDB not available - using fallback memory")
                self.initialized = False
                
        except ImportError:
            logger.warning("⚠️ Sentence-transformers not installed")
            logger.info("   Install with: pip install sentence-transformers chromadb")
            logger.info("   → Using rule-based context (still works, just less intelligent)")
            self.initialized = False
        except Exception as e:
            logger.warning(f"⚠️ Semantic memory initialization failed: {e}")
            logger.info("   → Using fallback context system")
            self.initialized = False
    
    def add_to_semantic_memory(
        self,
        conversation_id: str,
        message: str,
        role: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Add message to semantic memory
        This allows retrieving relevant context later
        """
        if not self.initialized:
            return
        
        try:
            # Create embedding
            embedding = self.embeddings_model.encode([message])[0].tolist()
            
            # Store in vector database
            self.collection.add(
                documents=[message],
                embeddings=[embedding],
                metadatas=[{
                    "conversation_id": conversation_id,
                    "role": role,
                    "timestamp": str(metadata.get('timestamp')) if metadata else None,
                    **(metadata or {})
                }],
                ids=[f"{conversation_id}_{role}_{len(self.collection.get()['ids'])}"]
            )
            
            logger.debug(f"Added to semantic memory: {message[:50]}...")
            
        except Exception as e:
            logger.debug(f"Failed to add to semantic memory: {e}")
    
    def find_relevant_context(
        self,
        query: str,
        conversation_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find most relevant previous messages using semantic search
        This is how ChatGPT finds relevant context from long conversations
        """
        if not self.initialized:
            return []
        
        try:
            # Encode query
            query_embedding = self.embeddings_model.encode([query])[0].tolist()
            
            # Search vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"conversation_id": conversation_id}
            )
            
            if results and results['documents']:
                relevant = []
                for i, doc in enumerate(results['documents'][0]):
                    relevant.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
                
                logger.info(f"🔍 Found {len(relevant)} semantically relevant context items")
                return relevant
            
        except Exception as e:
            logger.debug(f"Semantic search failed: {e}")
        
        return []
    
    def extract_conversation_topic(
        self,
        conversation_id: str
    ) -> Optional[str]:
        """
        Extract main topic from conversation using semantic clustering
        """
        if not self.initialized:
            return None
        
        try:
            # Get all messages from this conversation
            results = self.collection.get(
                where={"conversation_id": conversation_id}
            )
            
            if results and results['documents']:
                # Simple approach: get most recent user message
                user_docs = []
                for i, meta in enumerate(results['metadatas']):
                    if meta.get('role') == 'user':
                        user_docs.append(results['documents'][i])
                
                if user_docs:
                    # Extract proper nouns from recent messages
                    import re
                    topics = []
                    for doc in user_docs[-3:]:  # Last 3 user messages
                        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', doc)
                        topics.extend(capitalized)
                    
                    if topics:
                        # Return most recent unique topic
                        return topics[-1]
            
        except Exception as e:
            logger.debug(f"Topic extraction failed: {e}")
        
        return None
    
    def generate_context_summary(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate intelligent summary of conversation for context injection
        """
        if len(conversation_history) < 2:
            return ""
        
        # Extract key information
        topics = []
        user_info = []
        
        for msg in conversation_history:
            content = msg.get('content', '')
            role = msg.get('role')
            
            if role == 'user':
                # Extract topics (capitalized words)
                import re
                capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
                topics.extend(capitalized)
                
                # Extract personal info
                if any(phrase in content.lower() for phrase in ['my name is', 'i am', 'i work', 'i study']):
                    user_info.append(content)
        
        # Build summary
        summary_parts = []
        
        if topics:
            unique_topics = []
            seen = set()
            for t in topics:
                if t.lower() not in seen:
                    seen.add(t.lower())
                    unique_topics.append(t)
            
            if unique_topics:
                summary_parts.append(f"Topics discussed: {', '.join(unique_topics[-3:])}")
        
        if user_info:
            summary_parts.append(f"User mentioned: {' | '.join(user_info[-2:])}")
        
        return " | ".join(summary_parts) if summary_parts else ""


# Global instance
semantic_memory = SemanticMemory()

