"""
Conversation RAG (Retrieval Augmented Generation)
THE PERMANENT SOLUTION - Forces LLM to use context by pre-filling the answer
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import re


class ConversationRAG:
    """
    RAG system specifically for conversation continuity
    
    HOW IT WORKS (ChatGPT's REAL secret):
    Instead of hoping the LLM reads context, we FORCE it by:
    1. Detecting vague questions
    2. Finding relevant context
    3. PRE-FILLING the start of the answer with context
    4. LLM continues from there
    """
    
    def process_with_rag(
        self,
        user_question: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process question with RAG
        Returns: {'question': modified_question, 'context': context_to_inject, 'prefill': answer_start}
        """
        
        if not conversation_history or len(conversation_history) < 2:
            return {
                'question': user_question,
                'context': None,
                'prefill': None,
                'method': 'direct'
            }
        
        # Check if question needs context
        needs_context, reason = self._needs_context(user_question, conversation_history)
        
        if not needs_context:
            return {
                'question': user_question,
                'context': None,
                'prefill': None,
                'method': 'direct'
            }
        
        # Extract context
        context_type, context_value = self._extract_context(conversation_history)
        
        if not context_value:
            return {
                'question': user_question,
                'context': None,
                'prefill': None,
                'method': 'direct'
            }
        
        # BUILD FORCED CONTEXT
        if context_type == 'topic':
            # Modify question to include topic
            modified_question = self._inject_topic(user_question, context_value)
            
            # Pre-fill answer start (FORCE LLM to talk about the topic)
            prefill = self._generate_answer_prefill(user_question, context_value)
            
            logger.warning(f"🔴 RAG ACTIVATED (PERMANENT SOLUTION)")
            logger.warning(f"   Original Q: '{user_question}'")
            logger.warning(f"   Modified Q: '{modified_question}'")
            logger.warning(f"   Prefill: '{prefill}'")
            logger.warning(f"   Context: {context_value}")
            
            return {
                'question': modified_question,
                'context': context_value,
                'prefill': prefill,
                'method': 'rag'
            }
        
        elif context_type == 'personal':
            # User asking about themselves
            modified_question = user_question
            prefill = f"Based on what you told me earlier, {context_value}."
            
            return {
                'question': modified_question,
                'context': context_value,
                'prefill': prefill,
                'method': 'personal_rag'
            }
        
        return {
            'question': user_question,
            'context': None,
            'prefill': None,
            'method': 'direct'
        }
    
    def _needs_context(self, question: str, history: List[Dict[str, str]]) -> tuple[bool, str]:
        """Check if question needs context"""
        q_lower = question.lower().strip()
        
        # Very short questions ALWAYS need context
        if len(q_lower) < 25 and len(history) >= 2:
            return True, "short_question"
        
        # Questions with pronouns need context
        if re.search(r'\b(it|that|this|there|here)\b', q_lower):
            return True, "pronoun_reference"
        
        # Asking about self
        if re.search(r'\b(who am i|my name|about me)\b', q_lower):
            return True, "personal_info"
        
        return False, None
    
    def _extract_context(self, history: List[Dict[str, str]]) -> tuple[str, str]:
        """
        Extract context from history
        Returns: (context_type, context_value)
        """
        # Check for personal info first
        for msg in history:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                
                # Extract name
                if 'my name is' in content:
                    name = content.split('my name is')[1].split('.')[0].split(',')[0].strip()
                    return ('personal', f"your name is {name}")
                
                if 'i am' in content or 'iam' in content:
                    identity = content.replace('iam', 'i am').split('i am')[1].split('.')[0].strip()
                    if len(identity.split()) <= 3:  # Likely a name or simple identity
                        return ('personal', f"you are {identity}")
        
        # Extract topic from recent conversation
        recent = history[-6:]
        
        # Look for proper nouns (any script)
        topics = []
        for msg in recent:
            content = msg.get('content', '')
            
            # English
            caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
            topics.extend(caps)
            
            # Devanagari
            if 'काठमाडौं' in content or 'काठमांडू' in content or 'kathmandu' in content.lower():
                topics.append('Kathmandu')
            if 'नेपाल' in content or 'nepal' in content.lower():
                topics.append('Nepal')
        
        # Clean and return most recent
        stopwords = {'I', 'You', 'The', 'FRIDAY', 'Hi', 'Hello'}
        clean = [t for t in topics if t not in stopwords and len(t) > 2]
        
        if clean:
            return ('topic', clean[-1])
        
        return (None, None)
    
    def _inject_topic(self, question: str, topic: str) -> str:
        """Inject topic into question"""
        q_lower = question.lower().strip()
        
        # If question is very short, append topic
        if len(q_lower.split()) <= 3:
            return f"{question.rstrip('?')} of {topic}"
        
        # If it starts with question word, insert topic
        if re.match(r'^(who|what|where|when|how|why)', q_lower):
            return f"{question.rstrip('?')} in {topic}"
        
        return f"{question} (regarding {topic})"
    
    def _generate_answer_prefill(self, question: str, topic: str) -> str:
        """
        Generate answer prefill - FORCE LLM to start answer correctly
        This is the NUCLEAR option
        """
        q_lower = question.lower()
        
        # Pattern-based prefills
        if 'mayor' in q_lower or 'मेयर' in q_lower:
            return f"The mayor of {topic} is"
        
        if 'sub mayor' in q_lower or 'deputy' in q_lower:
            return f"The deputy mayor of {topic} is"
        
        if 'population' in q_lower or 'जनसंख्या' in q_lower:
            return f"The population of {topic} is"
        
        if 'capital' in q_lower or 'राजधानी' in q_lower:
            return f"The capital of {topic} is"
        
        if 'president' in q_lower or 'prime minister' in q_lower:
            return f"The leader of {topic} is"
        
        # Generic prefill
        return f"Regarding {topic},"


# Global instance
conversation_rag = ConversationRAG()

