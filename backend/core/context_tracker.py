"""
Advanced Context Tracker - ChatGPT-Level Intelligence
Automatically tracks conversation topics, understands intent, and maintains context
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger
import re


class ContextTracker:
    """
    Tracks conversation context automatically without manual training
    Identifies topics, entities, and maintains conversation flow
    """
    
    def __init__(self):
        self.current_topic = None
        self.entities_mentioned = []
        self.conversation_summary = ""
        self.last_user_intent = None
        self.topic_stack = []  # Stack of topics discussed
        self.user_preferences = {}  # Learn user preferences
        self.conversation_depth = 0  # Track how deep in a topic
    
    def extract_context(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        ADVANCED: Extract multi-layered conversation context
        - Intent detection
        - Follow-up detection
        - Ambiguity resolution
        - Multi-turn reasoning
        """
        if not conversation_history or len(conversation_history) < 2:
            return {
                "has_context": False,
                "current_topic": None,
                "entities": [],
                "summary": None,
                "intent": "general",
                "is_followup": False
            }
        
        # Get recent messages
        recent_messages = conversation_history[-8:]  # Extended window
        last_user_message = [m for m in conversation_history if m.get('role') == 'user'][-1]
        
        # ADVANCED ANALYSIS
        entities = self._extract_entities(recent_messages)
        topic = self._identify_topic(recent_messages)
        intent = self._detect_intent(last_user_message.get('content', ''))
        is_followup = self._is_followup_question(last_user_message.get('content', ''))
        ambiguity_hints = self._resolve_ambiguity(last_user_message.get('content', ''), entities, topic)
        user_prefs = self._detect_preferences(recent_messages)
        
        # Update topic stack
        if topic and (not self.topic_stack or self.topic_stack[-1] != topic):
            self.topic_stack.append(topic)
            if len(self.topic_stack) > 5:  # Keep last 5 topics
                self.topic_stack.pop(0)
        
        context = {
            "has_context": True,
            "current_topic": topic,
            "previous_topics": self.topic_stack[:-1] if len(self.topic_stack) > 1 else [],
            "entities": entities,
            "intent": intent,
            "is_followup": is_followup,
            "ambiguity_resolved": ambiguity_hints,
            "user_preferences": user_prefs,
            "conversation_depth": len(conversation_history),
            "summary": self._generate_smart_summary(recent_messages)
        }
        
        logger.info(f"🧠 Smart Context: Topic={topic}, Intent={intent}, Follow-up={is_followup}")
        logger.debug(f"   📍 Entities: {entities}")
        logger.debug(f"   💡 Ambiguity: {ambiguity_hints}")
        
        return context
    
    def _extract_entities(self, messages: List[Dict[str, str]]) -> List[str]:
        """
        Extract named entities (people, places, topics) from messages
        Simple keyword-based extraction (can be enhanced with NER)
        """
        entities = []
        
        # Keywords that indicate entities
        entity_indicators = [
            # Places
            'nepal', 'india', 'china', 'america', 'bangalore', 'kathmandu', 'delhi',
            'mumbai', 'london', 'tokyo', 'paris', 'new york',
            
            # Topics
            'python', 'javascript', 'ai', 'machine learning', 'programming',
            'college', 'university', 'school', 'job', 'career',
            'food', 'music', 'sports', 'movies', 'books',
            'mountains', 'rivers', 'cities', 'countries',
            
            # Technology
            'computer', 'software', 'hardware', 'app', 'website',
            
            # Education
            'cse', 'engineering', 'medical', 'science', 'arts'
        ]
        
        for msg in messages:
            content = msg.get('content', '').lower()
            for indicator in entity_indicators:
                if indicator in content and indicator not in entities:
                    entities.append(indicator)
        
        return entities[:5]  # Top 5 most recent entities
    
    def _identify_topic(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Identify the main topic being discussed
        """
        if not messages:
            return None
        
        # Get last user message for topic identification
        user_messages = [m for m in messages if m.get('role') == 'user']
        if not user_messages:
            return None
        
        last_user_msg = user_messages[-1].get('content', '').lower()
        
        # Topic detection based on keywords
        topics = {
            'nepal': ['nepal', 'kathmandu', 'everest', 'nepali'],
            'india': ['india', 'delhi', 'mumbai', 'indian'],
            'programming': ['code', 'programming', 'python', 'javascript', 'software'],
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml'],
            'education': ['college', 'university', 'study', 'course', 'degree'],
            'technology': ['computer', 'tech', 'app', 'website', 'digital'],
            'mountains': ['mountain', 'peak', 'himalaya', 'climb'],
            'travel': ['travel', 'trip', 'visit', 'tour', 'destination']
        }
        
        # Check all messages for topic
        all_content = ' '.join([m.get('content', '').lower() for m in messages])
        
        for topic, keywords in topics.items():
            if any(keyword in all_content for keyword in keywords):
                return topic
        
        return None
    
    def _detect_intent(self, message: str) -> str:
        """
        Detect user's intent from their message
        """
        message_lower = message.lower().strip()
        
        # Intent patterns
        if any(word in message_lower for word in ['what', 'tell', 'explain', 'describe', 'define']):
            return 'information_seeking'
        elif any(word in message_lower for word in ['how', 'tutorial', 'guide', 'steps']):
            return 'instruction_seeking'
        elif any(word in message_lower for word in ['why', 'reason', 'because']):
            return 'explanation_seeking'
        elif any(word in message_lower for word in ['compare', 'difference', 'vs', 'versus', 'better']):
            return 'comparison'
        elif any(word in message_lower for word in ['recommend', 'suggest', 'best', 'should i']):
            return 'recommendation'
        elif any(word in message_lower for word in ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok']):
            return 'affirmation'
        elif any(word in message_lower for word in ['more', 'details', 'elaborate', 'continue']):
            return 'elaboration_request'
        elif message_lower.endswith('?'):
            return 'question'
        else:
            return 'statement'
    
    def _is_followup_question(self, message: str) -> bool:
        """
        Detect if this is a follow-up question
        """
        message_lower = message.lower().strip()
        
        # Follow-up indicators
        followup_patterns = [
            # Vague references
            r'\b(it|that|this|these|those|them|its|their)\b',
            # Short questions
            r'^(yes|yeah|yep|no|nope|sure|okay|ok)[\s\?]*$',
            r'^(more|tell me more|what about|how about|and|also)\b',
            # Pronouns without context
            r'^(what|where|when|who|why|how)[\s\?]*$',
            # Continuation words
            r'\b(also|additionally|furthermore|moreover|besides)\b',
        ]
        
        for pattern in followup_patterns:
            if re.search(pattern, message_lower):
                return True
        
        # Short questions (< 15 chars) are likely follow-ups
        if len(message.strip()) < 15 and '?' in message:
            return True
        
        return False
    
    def _resolve_ambiguity(self, message: str, entities: List[str], topic: Optional[str]) -> str:
        """
        Resolve ambiguous pronouns and references
        """
        message_lower = message.lower()
        hints = []
        
        # Pronoun resolution
        pronouns = {
            'it': 'the previously mentioned topic',
            'that': 'what we just discussed',
            'this': 'the current subject',
            'they': 'the mentioned entities',
            'them': 'the things discussed'
        }
        
        for pronoun, resolution in pronouns.items():
            if re.search(rf'\b{pronoun}\b', message_lower):
                if topic:
                    hints.append(f"'{pronoun}' likely refers to {topic}")
                elif entities:
                    hints.append(f"'{pronoun}' likely refers to {', '.join(entities[:2])}")
        
        # Vague questions
        if message_lower in ['yes', 'yeah', 'ok', 'sure', 'more', 'tell me more']:
            hints.append(f"User wants more information about {topic if topic else 'previous topic'}")
        
        if message_lower.startswith('what about') or message_lower.startswith('how about'):
            if topic:
                hints.append(f"User asking about an aspect of {topic}")
        
        return ' | '.join(hints) if hints else 'No ambiguity detected'
    
    def _detect_preferences(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Learn user preferences from conversation
        """
        prefs = {}
        
        for msg in messages:
            if msg.get('role') != 'user':
                continue
                
            content = msg.get('content', '').lower()
            
            # Detect preferences
            if any(word in content for word in ['i like', 'i love', 'i prefer', 'i enjoy']):
                prefs['interests'] = prefs.get('interests', [])
                # Extract what they like
                words = content.split()
                for i, word in enumerate(words):
                    if word in ['like', 'love', 'prefer', 'enjoy'] and i + 1 < len(words):
                        prefs['interests'].append(words[i + 1])
            
            # Detect personal info
            if 'my name is' in content or 'i am' in content:
                prefs['has_personal_info'] = True
            
            # Detect expertise level
            if any(word in content for word in ['beginner', 'new to', 'learning', 'start']):
                prefs['expertise_level'] = 'beginner'
            elif any(word in content for word in ['expert', 'advanced', 'experienced']):
                prefs['expertise_level'] = 'advanced'
        
        return prefs
    
    def _generate_smart_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate intelligent summary focusing on key points
        """
        if not messages:
            return ""
        
        # Extract key information
        key_points = []
        for msg in messages[-4:]:
            content = msg.get('content', '')
            role = msg.get('role')
            
            # Extract first sentence or main point
            if role == 'user':
                first_sentence = content.split('.')[0].split('?')[0][:80]
                key_points.append(f"👤 {first_sentence}")
            elif role == 'assistant' and len(key_points) < 3:
                first_sentence = content.split('.')[0][:80]
                key_points.append(f"🤖 {first_sentence}")
        
        return " → ".join(key_points[-3:])  # Last 3 key points
    
    def build_context_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build ADVANCED context-aware prompt with intelligent reasoning
        """
        if not context.get('has_context'):
            return ""
        
        topic = context.get('current_topic')
        entities = context.get('entities', [])
        intent = context.get('intent')
        is_followup = context.get('is_followup')
        ambiguity = context.get('ambiguity_resolved')
        prefs = context.get('user_preferences', {})
        prev_topics = context.get('previous_topics', [])
        
        prompt_parts = []
        
        prompt_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        prompt_parts.append("🧠 INTELLIGENT CONTEXT ANALYSIS (ChatGPT-Level)")
        prompt_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Current Topic
        if topic:
            prompt_parts.append(f"\n📌 ACTIVE TOPIC: **{topic.upper()}**")
            prompt_parts.append(f"   → All responses should relate to {topic}")
            prompt_parts.append(f"   → User is currently exploring this subject")
        
        # Previous Topics (Breadcrumbs)
        if prev_topics:
            prompt_parts.append(f"\n🔙 CONVERSATION FLOW: {' → '.join(prev_topics[-3:])} → {topic}")
        
        # Entities Mentioned
        if entities:
            prompt_parts.append(f"\n📍 KEY ENTITIES: {', '.join(entities)}")
            prompt_parts.append(f"   → These are the specific subjects being discussed")
        
        # Intent Detection
        prompt_parts.append(f"\n🎯 USER INTENT: {intent}")
        if intent == 'information_seeking':
            prompt_parts.append("   → Provide factual, informative answer")
        elif intent == 'instruction_seeking':
            prompt_parts.append("   → Give step-by-step guidance")
        elif intent == 'elaboration_request':
            prompt_parts.append("   → Expand on previous response with more details")
        elif intent == 'affirmation':
            prompt_parts.append("   → User agrees, continue with related information")
        elif intent == 'recommendation':
            prompt_parts.append("   → Suggest best options based on context")
        
        # Follow-up Detection
        if is_followup:
            prompt_parts.append(f"\n⚡ FOLLOW-UP DETECTED!")
            prompt_parts.append(f"   → This question relates to previous discussion about {topic}")
            prompt_parts.append(f"   → DO NOT answer generically - use conversation context")
            prompt_parts.append(f"   → Example: If user asked about Nepal, then 'mountains' = mountains IN Nepal")
        
        # Ambiguity Resolution
        if ambiguity and 'No ambiguity' not in ambiguity:
            prompt_parts.append(f"\n💡 AMBIGUITY HINTS: {ambiguity}")
        
        # User Preferences
        if prefs:
            prompt_parts.append(f"\n👤 USER PROFILE:")
            if 'expertise_level' in prefs:
                prompt_parts.append(f"   → Level: {prefs['expertise_level']}")
            if 'interests' in prefs and prefs['interests']:
                prompt_parts.append(f"   → Interests: {', '.join(prefs['interests'][:3])}")
        
        # Final Instructions
        prompt_parts.append("\n" + "━" * 50)
        prompt_parts.append("⚡ CRITICAL INSTRUCTION:")
        prompt_parts.append("Use ALL the context above to provide a RELEVANT, CONNECTED response.")
        prompt_parts.append("Think: What is the user REALLY asking based on conversation flow?")
        prompt_parts.append("━" * 50 + "\n")
        
        return "\n".join(prompt_parts)


# Global instance
context_tracker = ContextTracker()

