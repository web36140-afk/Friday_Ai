"""
ChatGPT-Exact Context System
The ACTUAL method ChatGPT uses for perfect context continuity
"""
from typing import List, Dict, Any
from loguru import logger
import re


def build_chatgpt_style_messages(
    user_question: str,
    conversation_history: List[Dict[str, str]],
    system_prompt: str
) -> List[Dict[str, str]]:
    """
    Build messages EXACTLY like ChatGPT does
    
    ChatGPT's Secret: They inject context DIRECTLY into the conversation,
    not just in system prompts (which LLMs sometimes ignore)
    """
    
    # ENHANCED SYSTEM PROMPT - Force memory usage
    enhanced_system = f"""{system_prompt}

🧠 CRITICAL MEMORY RULE:
- You MUST remember EVERYTHING the user tells you in this conversation
- If user says "I am X", you MUST remember X
- If user asks "who am I?", answer with what they told you earlier
- READ THE CONVERSATION HISTORY CAREFULLY before answering

Example:
User: "I am Dipesh"
You: [acknowledge]
User: "who am I?"
You: ✅ "You're Dipesh" (from conversation history)
You: ❌ "I don't know" (WRONG - you have the history!)
"""
    
    messages = [{"role": "system", "content": enhanced_system}]
    
    # Add full conversation history
    logger.info(f"📚 Adding {len(conversation_history)} previous messages to context")
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
        logger.debug(f"   → {msg['role']}: {msg['content'][:50]}...")
    
    # CHATGPT'S SECRET: For vague questions, inject context AS A SYSTEM MESSAGE
    # right before the user's question
    if len(conversation_history) >= 2:
        # Check for personal information first (names, etc.)
        personal_info = extract_personal_info(conversation_history)
        if personal_info and is_asking_about_self(user_question):
            # User is asking about themselves - remind the AI
            context_injection = f"""[PERSONAL INFO CONTEXT]
The user previously told you: {personal_info}
Their current question "{user_question}" is asking about themselves.
You MUST answer using the information they gave you earlier.
DO NOT say "I don't know" - you have the conversation history above!"""
            
            messages.append({
                "role": "system",
                "content": context_injection
            })
            
            logger.warning(f"🔴 PERSONAL INFO: User asking about themselves")
            logger.warning(f"   → Info: {personal_info}")
        
        # Extract current topic
        topic = extract_current_topic(conversation_history)
        
        # Check if question is vague
        if is_vague_question(user_question) and topic:
            # INJECT CONTEXT MESSAGE
            context_injection = f"""[TOPIC CONTEXT]
Current conversation topic: {topic}
User's next message "{user_question}" is asking about {topic}.
You MUST answer about {topic}, not in general.
Example: If they ask "mayor", answer about the mayor OF {topic}."""
            
            messages.append({
                "role": "system",
                "content": context_injection
            })
            
            logger.warning(f"🔴 TOPIC CONTEXT: Injected for '{user_question}'")
            logger.warning(f"   → Topic: {topic}")
    
    # ULTRA-AGGRESSIVE: Rewrite vague questions to include context
    final_question = user_question
    
    if is_vague_question(user_question) and topic:
        # REWRITE the question to be EXPLICIT
        final_question = rewrite_question_with_context(user_question, topic)
        logger.warning(f"🔴 QUESTION REWRITTEN:")
        logger.warning(f"   Original: '{user_question}'")
        logger.warning(f"   Rewritten: '{final_question}'")
    
    # Add user's question (REWRITTEN if vague)
    messages.append({
        "role": "user",
        "content": final_question
    })
    
    return messages


def rewrite_question_with_context(question: str, topic: str) -> str:
    """
    AGGRESSIVELY rewrite question to include context
    This is the NUCLEAR option - actually change the question
    """
    q_lower = question.lower().strip()
    
    # Single word or very short questions
    if len(q_lower.split()) <= 3:
        # Add topic explicitly
        return f"{question.rstrip('?')} of {topic}?"
    
    # Questions starting with "who", "what", "where" etc without subject
    if re.match(r'^(who|what|where|when|how|why)\s+(is|are|was|were)\s+\w+', q_lower):
        # Insert topic
        words = question.split()
        if len(words) <= 4:
            return f"{question.rstrip('?')} in {topic}?"
    
    return question


def extract_current_topic(conversation_history: List[Dict[str, str]]) -> str:
    """Extract current topic from conversation"""
    if not conversation_history:
        return None
    
    # Look at last 4 messages
    recent = conversation_history[-4:]
    
    # Extract ALL proper nouns and Devanagari place names
    topics = []
    
    for msg in recent:
        content = msg.get('content', '')
        
        # English proper nouns
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        topics.extend(capitalized)
        
        # Devanagari patterns
        if 'काठमाडौं' in content or 'काठमांडू' in content:
            topics.append('Kathmandu')
        if 'नेपाल' in content:
            topics.append('Nepal')
        if 'भारत' in content or 'इंडिया' in content:
            topics.append('India')
    
    # Remove common words
    stopwords = {'I', 'You', 'The', 'My', 'Is', 'Are', 'FRIDAY', 'Hello', 'Hi'}
    clean_topics = [t for t in topics if t not in stopwords and len(t) > 2]
    
    # Return most recent
    if clean_topics:
        return clean_topics[-1]
    
    # Fallback: search lowercase
    all_text = ' '.join([m.get('content', '').lower() for m in recent])
    
    if 'kathmandu' in all_text or 'काठमाडौं' in all_text:
        return 'Kathmandu'
    if 'nepal' in all_text or 'नेपाल' in all_text:
        return 'Nepal'
    if 'python' in all_text:
        return 'Python'
    
    return None


def extract_personal_info(conversation_history: List[Dict[str, str]]) -> str:
    """Extract personal information user shared"""
    info_parts = []
    
    for msg in conversation_history:
        if msg.get('role') != 'user':
            continue
        
        content = msg.get('content', '').lower()
        
        # Name patterns
        if 'my name is' in content or 'i am' in content or 'iam' in content:
            # Extract the name/info
            if 'my name is' in content:
                name = content.split('my name is')[1].split('.')[0].split(',')[0].strip()
                info_parts.append(f"name is {name}")
            elif 'i am' in content or 'iam' in content:
                info_text = content.replace('iam', 'i am')
                identity = info_text.split('i am')[1].split('.')[0].split(',')[0].strip()
                info_parts.append(f"they are {identity}")
        
        # Job/role
        if 'i work' in content or 'i study' in content:
            info_parts.append(content.split('.')[0])
    
    return ' | '.join(info_parts) if info_parts else None


def is_asking_about_self(question: str) -> bool:
    """Check if user is asking about themselves"""
    q_lower = question.lower()
    
    patterns = [
        r'\bwho am i\b',
        r'\bwhat.*my name\b',
        r'\bwho.*i\b',
        r'\btell.*about me\b',
        r'\bwhat do i\b'
    ]
    
    for pattern in patterns:
        if re.search(pattern, q_lower):
            return True
    
    return False


def is_vague_question(question: str) -> bool:
    """Check if question is vague and needs context"""
    q = question.strip().lower()
    
    # Single word
    if len(q.split()) == 1:
        return True
    
    # Very short (< 20 chars) - INCREASED threshold
    if len(q) < 20:
        return True
    
    # Short questions with no specific subject mentioned
    if len(q.split()) <= 4:
        # If it doesn't mention a proper noun, it's vague
        if not re.search(r'\b[A-Z][a-z]+', question):
            return True
    
    # Common vague patterns
    vague = ['yes', 'yeah', 'ok', 'more', 'what about', 'tell me', 'and', 'also']
    if any(q.startswith(v) for v in vague):
        return True
    
    return False

