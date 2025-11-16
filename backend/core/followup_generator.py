"""
Follow-up Question Generator
Suggests relevant next questions like ChatGPT
"""
from typing import List, Dict, Any
from loguru import logger


class FollowupGenerator:
    """
    Generates intelligent follow-up question suggestions
    Like ChatGPT's "Continue the conversation" feature
    """
    
    def generate_followups(
        self,
        last_response: str,
        current_topic: str,
        conversation_history: List[Dict[str, str]]
    ) -> List[str]:
        """
        Generate 3-5 relevant follow-up questions
        """
        followups = []
        
        if not current_topic:
            return []
        
        topic_lower = current_topic.lower()
        
        # Topic-specific follow-ups
        topic_followups = {
            'kathmandu': [
                "What are the top tourist attractions in Kathmandu?",
                "What is the culture like in Kathmandu?",
                "How's the food in Kathmandu?",
                "What languages are spoken in Kathmandu?"
            ],
            'nepal': [
                "What are the best places to visit in Nepal?",
                "Tell me about Mount Everest",
                "What is Nepal's history?",
                "What languages are spoken in Nepal?"
            ],
            'python': [
                "What are the best Python libraries?",
                "How do I start learning Python?",
                "Show me a Python example",
                "What can I build with Python?"
            ],
            'ai': [
                "How does AI work?",
                "What are the types of AI?",
                "How can I learn AI?",
                "What are AI applications?"
            ],
            'programming': [
                "What programming language should I learn first?",
                "How to become a good programmer?",
                "Best programming resources?",
                "What are programming paradigms?"
            ]
        }
        
        # Check if we have predefined follow-ups for this topic
        for topic_key, questions in topic_followups.items():
            if topic_key in topic_lower:
                followups.extend(questions[:3])
                break
        
        # Generic follow-ups based on conversation depth
        if not followups:
            followups = [
                f"Tell me more about {current_topic}",
                f"What else should I know about {current_topic}?",
                f"Can you give an example related to {current_topic}?"
            ]
        
        # Add contextual follow-ups based on response content
        if 'history' not in last_response.lower() and len(followups) < 4:
            followups.append(f"What's the history of {current_topic}?")
        
        if any(word in last_response.lower() for word in ['place', 'location', 'city']) and len(followups) < 4:
            followups.append(f"Where can I find more information about {current_topic}?")
        
        return followups[:4]  # Return top 4


# Global instance
followup_generator = FollowupGenerator()

