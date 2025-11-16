"""
Automatic Tool Calling - Like Perplexity
AI automatically decides when to use tools (web search, files, etc.)
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import re


class AutoToolCaller:
    """
    Automatically triggers tools based on query analysis
    Makes FRIDAY act like Perplexity - auto-searches when needed
    """
    
    def analyze_and_suggest_tools(
        self,
        question: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze question and suggest which tools to use automatically
        
        Returns: List of tool calls to make
        """
        tools_to_call = []
        q_lower = question.lower()
        
        # 1. WEB SEARCH - Trigger for current/factual information
        if self._needs_web_search(q_lower, context):
            tools_to_call.append({
                'tool': 'web_search',
                'operation': 'web_search',
                'arguments': {
                    'query': question,
                    'provider': 'duckduckgo',
                    'max_results': 5
                },
                'reason': 'Question requires current/factual information from the web'
            })
        
        # 2. WEATHER - Auto-trigger for weather queries
        if self._is_weather_query(q_lower):
            city = self._extract_city(question) or 'Bangalore'
            tools_to_call.append({
                'tool': 'weather_news',
                'operation': 'weather',
                'arguments': {
                    'city': city,
                    'country': 'IN'
                },
                'reason': f'Weather information requested for {city}'
            })
        
        # 3. NEWS - Auto-trigger for news queries
        if self._is_news_query(q_lower):
            if 'about' in q_lower or 'on' in q_lower:
                # News search with topic
                topic = self._extract_news_topic(question)
                tools_to_call.append({
                    'tool': 'weather_news',
                    'operation': 'news_search',
                    'arguments': {
                        'query': topic or question,
                        'max_results': 5
                    },
                    'reason': f'News search for: {topic or question}'
                })
            else:
                # General latest news
                tools_to_call.append({
                    'tool': 'weather_news',
                    'operation': 'news',
                    'arguments': {
                        'country': 'in',
                        'category': 'general'
                    },
                    'reason': 'Latest news requested'
                })
        
        # 4. SYSTEM INFO - Auto-trigger for system queries
        if self._is_system_query(q_lower):
            tools_to_call.append({
                'tool': 'hardware_monitor',
                'operation': 'all',
                'arguments': {},
                'reason': 'System information requested'
            })
        
        # 5. FILE SEARCH - Auto-trigger for file-related queries
        if self._is_file_query(q_lower):
            pattern = self._extract_file_pattern(question)
            tools_to_call.append({
                'tool': 'file_operations',
                'operation': 'search',
                'arguments': {
                    'path': '.',
                    'pattern': pattern or '*',
                    'content_search': None
                },
                'reason': f'File search for: {pattern or "all files"}'
            })
        
        if tools_to_call:
            logger.info(f"🤖 AUTO-TOOL TRIGGER: {len(tools_to_call)} tool(s) suggested")
            for tool in tools_to_call:
                logger.info(f"   → {tool['tool']}: {tool['reason']}")
        
        return tools_to_call
    
    def _needs_web_search(self, question: str, context: Dict[str, Any]) -> bool:
        """Determine if question needs real-time web search"""
        
        # Keywords that indicate need for current information
        web_triggers = [
            'latest', 'current', 'recent', 'today', 'news', 'now',
            'what is happening', 'update', 'this year', '2024', '2025',
            'price of', 'cost of', 'how much', 'where to buy',
            'best', 'top', 'recommend', 'comparison',
            'who is', 'what is', 'where is' # Factual queries
        ]
        
        # Check for triggers
        for trigger in web_triggers:
            if trigger in question:
                return True
        
        # Questions about specific people/places/events (likely need web)
        if re.search(r'\b(mayor|president|ceo|founder|leader)\b', question, re.IGNORECASE):
            return True
        
        # Factual "what is" questions
        if re.match(r'^(what|who|where|when)\s+is\b', question, re.IGNORECASE):
            # But not for well-known concepts
            common_concepts = ['ai', 'python', 'programming', 'computer']
            if not any(concept in question for concept in common_concepts):
                return True
        
        return False
    
    def _is_weather_query(self, question: str) -> bool:
        """Check if question is about weather"""
        weather_keywords = [
            'weather', 'temperature', 'rain', 'forecast',
            'hot', 'cold', 'sunny', 'cloudy', 'climate'
        ]
        return any(keyword in question for keyword in weather_keywords)
    
    def _is_news_query(self, question: str) -> bool:
        """Check if question is about news"""
        news_keywords = [
            'news', 'headlines', 'latest news', 'breaking',
            'happening', 'updates', 'current events'
        ]
        return any(keyword in question for keyword in news_keywords)
    
    def _is_system_query(self, question: str) -> bool:
        """Check if question is about system status"""
        system_keywords = [
            'cpu', 'ram', 'memory', 'disk', 'battery',
            'system status', 'performance', 'usage'
        ]
        return any(keyword in question for keyword in system_keywords)
    
    def _is_file_query(self, question: str) -> bool:
        """Check if question is about files"""
        file_keywords = [
            'file', 'folder', 'directory', 'find file',
            'search file', 'locate', 'where is my'
        ]
        return any(keyword in question for keyword in file_keywords)
    
    def _extract_city(self, question: str) -> Optional[str]:
        """Extract city name from weather query"""
        common_cities = ['bangalore', 'delhi', 'mumbai', 'kathmandu', 'london', 'new york']
        for city in common_cities:
            if city in question.lower():
                return city.title()
        return None
    
    def _extract_news_topic(self, question: str) -> str:
        """Extract news topic from question"""
        # Remove common words
        words = question.lower().split()
        stopwords = ['news', 'about', 'on', 'latest', 'the', 'a', 'an']
        topic_words = [w for w in words if w not in stopwords and len(w) > 2]
        return ' '.join(topic_words[:3]) if topic_words else question
    
    def _extract_file_pattern(self, question: str) -> str:
        """Extract file pattern from query"""
        # Look for file extensions
        extensions = re.findall(r'\.(txt|pdf|doc|docx|xls|xlsx|py|js|html|css)', question, re.IGNORECASE)
        if extensions:
            return f'*{extensions[0]}'
        
        # Look for filenames
        filenames = re.findall(r'["\'](.*?)["\']', question)
        if filenames:
            return filenames[0]
        
        return '*'


# Global instance
auto_tool_caller = AutoToolCaller()

