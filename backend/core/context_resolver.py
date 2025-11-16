"""
Mandatory Context Resolver
FORCES the LLM to understand context by explicitly rewriting vague questions
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import re


class ContextResolver:
    """
    Explicitly resolves vague/ambiguous questions using conversation context
    Rewrites questions to be fully contextual BEFORE sending to LLM
    """
    
    def resolve_question(
        self,
        question: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Resolve vague question into explicit, contextual question
        
        Example:
        User: "Tell me about Kathmandu"
        User: "mayor?" 
        → Resolved: "Who is the mayor of Kathmandu?" or "Tell me about the mayor of Kathmandu"
        """
        
        if not conversation_history or len(conversation_history) < 2:
            return {
                'original': question,
                'resolved': question,
                'is_vague': False,
                'context_used': None
            }
        
        # Check if question is vague/context-dependent
        is_vague = self._is_vague_question(question)
        
        if not is_vague:
            return {
                'original': question,
                'resolved': question,
                'is_vague': False,
                'context_used': None
            }
        
        # Extract context from recent messages
        context_topic = self._extract_topic_from_history(conversation_history)
        context_entities = self._extract_entities_from_history(conversation_history)
        
        if not context_topic and not context_entities:
            return {
                'original': question,
                'resolved': question,
                'is_vague': True,
                'context_used': None
            }
        
        # REWRITE the question to be explicit
        resolved_question = self._rewrite_with_context(
            question,
            context_topic,
            context_entities
        )
        
        logger.info(f"🔄 Context Resolution:")
        logger.info(f"   Original: '{question}'")
        logger.info(f"   Resolved: '{resolved_question}'")
        logger.info(f"   Context: {context_topic or ', '.join(context_entities[:2])}")
        
        return {
            'original': question,
            'resolved': resolved_question,
            'is_vague': True,
            'context_used': context_topic or ', '.join(context_entities[:2])
        }
    
    def _is_vague_question(self, question: str) -> bool:
        """Check if question is vague and needs context"""
        q_lower = question.lower().strip()
        
        # Very short questions
        if len(q_lower) < 20 and '?' in question:
            return True
        
        # Single word questions
        if len(q_lower.split()) <= 2:
            return True
        
        # Vague patterns
        vague_patterns = [
            r'^(what|where|when|who|why|how)\s*\?*$',
            r'^(it|that|this|there|here)\b',
            r'^(more|tell me more|continue|yes|yeah|ok)\b',
            r'^(about|regarding)\b',
            r'^\w+\?$',  # Single word with question mark
        ]
        
        for pattern in vague_patterns:
            if re.search(pattern, q_lower):
                return True
        
        return False
    
    def _extract_topic_from_history(self, history: List[Dict[str, str]]) -> Optional[str]:
        """Extract main topic from recent conversation - Works with ALL languages"""
        if not history or len(history) < 2:
            return None
        
        # Look at last few messages
        recent = history[-6:] if len(history) >= 6 else history
        
        # Extract ALL proper nouns (English capitalized OR Devanagari)
        all_topics = []
        for msg in recent:
            content = msg.get('content', '')
            
            # Extract English proper nouns (capitalized)
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
            all_topics.extend(capitalized)
            
            # Extract Devanagari proper nouns (common place names)
            devanagari_patterns = {
                'kathmandu': [r'काठमाडौं', r'काठमांडू', r'काठमाण्डौं'],
                'nepal': [r'नेपाल'],
                'india': [r'भारत', r'इंडिया'],
                'china': [r'चीन'],
            }
            
            for topic_en, patterns in devanagari_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        all_topics.append(topic_en)
        
        # Remove common words
        stopwords = {'I', 'You', 'The', 'A', 'An', 'In', 'On', 'At', 'To', 'For', 'Of', 'And', 'Or', 'But', 'Is', 'Are', 'Was', 'Were', 'Be', 'Been', 'Being', 'FRIDAY'}
        topics = [t for t in all_topics if t not in stopwords and len(t) > 2]
        
        if topics:
            # Return most recent topic
            logger.info(f"🎯 Extracted topic from history: {topics[-1]}")
            return topics[-1]
        
        # Fallback: Look for common patterns in ANY script
        all_text_lower = ' '.join([m.get('content', '').lower() for m in recent])
        
        # English + Devanagari patterns
        topic_patterns = {
            'kathmandu': r'(kathmandu|काठमाडौं|काठमांडू)',
            'nepal': r'(nepal|नेपाल)',
            'india': r'(india|भारत|इंडिया)',
            'python': r'\bpython\b',
            'javascript': r'\bjavascript\b',
            'ai': r'\b(ai|artificial intelligence)\b',
        }
        
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, all_text_lower, re.IGNORECASE):
                logger.info(f"🎯 Found topic via pattern: {topic}")
                return topic
        
        return None
    
    def _extract_entities_from_history(self, history: List[Dict[str, str]]) -> List[str]:
        """Extract named entities from history"""
        entities = []
        
        # Get last 2 messages
        recent = history[-4:] if len(history) >= 4 else history
        
        entity_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Capitalized words
        ]
        
        for msg in recent:
            content = msg.get('content', '')
            for pattern in entity_patterns:
                matches = re.findall(pattern, content)
                entities.extend(matches)
        
        # Remove duplicates, keep order
        seen = set()
        unique_entities = []
        for e in entities:
            if e.lower() not in seen and len(e) > 2:
                seen.add(e.lower())
                unique_entities.append(e)
        
        return unique_entities[:5]
    
    def _rewrite_with_context(
        self,
        question: str,
        topic: Optional[str],
        entities: List[str]
    ) -> str:
        """Rewrite vague question with explicit context - AGGRESSIVE rewriting"""
        q_lower = question.lower().strip()
        
        context_subject = topic or (entities[0] if entities else None)
        
        if not context_subject:
            return question
        
        # AGGRESSIVE Pattern-based rewriting
        
        # Single word questions - BE ULTRA EXPLICIT
        if re.match(r'^\w+\?*$', q_lower) or len(q_lower.split()) == 1:
            word = q_lower.rstrip('?').strip()
            
            logger.warning(f"🔴 SINGLE WORD QUESTION DETECTED: '{word}'")
            logger.warning(f"   → Context: {context_subject}")
            
            # Common single-word questions with EXPLICIT rewriting
            if word in ['mayor', 'मेयर', 'meyor']:
                resolved = f"Who is the current mayor of {context_subject}? What is their name and tell me about the mayor of {context_subject} city."
                logger.warning(f"   → Resolved to: {resolved}")
                return resolved
            elif word in ['population', 'जनसंख्या']:
                return f"What is the population of {context_subject}?"
            elif word in ['history', 'इतिहास']:
                return f"Tell me about the history of {context_subject}"
            elif word in ['culture', 'संस्कृति']:
                return f"Tell me about the culture of {context_subject}"
            else:
                return f"Tell me about the {word} of {context_subject}"
        
        # Very short questions (2-3 words)
        if len(q_lower.split()) <= 3 and '?' in question:
            return f"{question.rstrip('?')} of {context_subject}?"
        
        # Questions starting with question words but no subject
        if re.match(r'^(what|where|when|who|how|why)\s+\w+\s*\?*$', q_lower):
            return f"{question.rstrip('?')} in {context_subject}?"
        
        # "What about X?" → "What about X in context?"
        if q_lower.startswith('what about') or q_lower.startswith('how about'):
            return f"{question.rstrip('?')} in {context_subject}?"
        
        # Add context to ANY short question
        if len(q_lower) < 20:
            # Remove trailing question mark and add context
            clean_q = question.rstrip('?').strip()
            return f"{clean_q} (specifically related to {context_subject})?"
        
        return question


# Global instance
context_resolver = ContextResolver()

