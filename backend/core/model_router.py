"""
Intelligent Model Router
Automatically selects the best AI model based on question complexity and context
"""
from typing import Dict, Any, Optional
from loguru import logger


class ModelRouter:
    """
    Routes questions to the most appropriate AI model
    - Simple questions → Fast model (Groq Llama 3.3 70B)
    - Complex/reasoning → Advanced model (Groq Llama 3.3 70B or GPT-4 if available)
    - Multilingual (Hindi/Nepali) → Gemini
    """
    
    def __init__(self):
        self.model_capabilities = {
            'llama-3.3-70b-versatile': {
                'speed': 'fast',
                'reasoning': 'excellent',
                'context_window': 32768,
                'languages': ['en'],
                'cost': 'low',
                'best_for': ['general', 'reasoning', 'code', 'fast_response']
            },
            'gemini-2.5-flash': {
                'speed': 'very_fast',
                'reasoning': 'excellent',
                'context_window': 1000000,
                'languages': ['en', 'hi', 'ne', 'multi'],
                'cost': 'free',
                'best_for': ['multilingual', 'hindi', 'nepali', 'conversation', 'context', 'speed']
            },
            'gpt-4-turbo-preview': {
                'speed': 'slow',
                'reasoning': 'exceptional',
                'context_window': 128000,
                'languages': ['en', 'multi'],
                'cost': 'high',
                'best_for': ['complex_reasoning', 'analysis', 'creative']
            }
        }
    
    def select_best_model(
        self,
        question: str,
        language: str,
        context: Dict[str, Any],
        user_preference: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Intelligently select the best model for the question
        
        GEMINI is BETTER at:
        - Context awareness
        - Following instructions
        - Multilingual
        - FREE with high limits
        
        GROQ is BETTER at:
        - Speed
        - Code generation
        - Technical questions
        """
        
        # User preference overrides (if specified)
        if user_preference:
            return self._get_model_config(user_preference)
        
        # Language-based routing (Always use Gemini for non-English)
        if language in ['hi-IN', 'hindi', 'ne-NP', 'nepali']:
            logger.info(f"🌍 Using Gemini for {language} (better multilingual)")
            return {'provider': 'gemini', 'model': 'gemini-2.5-flash'}
        
        # CONTEXT-DEPENDENT questions → Use Gemini (better at context)
        if context.get('is_followup') or context.get('intent') == 'elaboration_request':
            logger.info("🧠 Using Gemini for context-heavy question (better at memory)")
            return {'provider': 'gemini', 'model': 'gemini-2.5-flash'}
        
        # Short/vague questions → Use Gemini (better at inference)
        if len(question.strip()) < 25:
            logger.info("🔍 Using Gemini for short question (better at context)")
            return {'provider': 'gemini', 'model': 'gemini-2.5-flash'}
        
        # Complexity-based routing for English
        complexity = self._analyze_complexity(question, context)
        
        if complexity == 'simple':
            # Simple factual → Groq (faster)
            logger.info("⚡ Using Groq for simple question (faster)")
            return {'provider': 'groq', 'model': 'llama-3.3-70b-versatile'}
        
        elif complexity == 'medium':
            # Medium → Gemini (better overall)
            logger.info("🧠 Using Gemini for balanced performance")
            return {'provider': 'gemini', 'model': 'gemini-2.5-flash'}
        
        elif complexity == 'complex':
            # Complex → Gemini (better at reasoning with context)
            logger.info("🎓 Using Gemini for complex reasoning")
            return {'provider': 'gemini', 'model': 'gemini-2.5-flash'}
        
        # Default: Gemini (better at context overall)
        logger.info("🔵 Using Gemini (default - best for conversations)")
        return {'provider': 'gemini', 'model': 'gemini-1.5-flash'}
    
    def _analyze_complexity(self, question: str, context: Dict[str, Any]) -> str:
        """
        Analyze question complexity
        Returns: 'simple', 'medium', or 'complex'
        """
        question_lower = question.lower().strip()
        
        # Simple question indicators
        simple_patterns = [
            'what is',
            'who is',
            'where is',
            'when',
            'define',
            'meaning of'
        ]
        
        # Complex question indicators
        complex_patterns = [
            'analyze',
            'compare',
            'evaluate',
            'design',
            'create',
            'develop',
            'explain why',
            'how does',
            'pros and cons',
            'advantages and disadvantages',
            'step by step',
            'best way to',
            'optimize'
        ]
        
        # Check length
        word_count = len(question.split())
        
        # Very short = simple
        if word_count < 8:
            # But check if it's a follow-up (which needs context)
            if context.get('is_followup'):
                return 'medium'
            return 'simple'
        
        # Check patterns
        if any(pattern in question_lower for pattern in complex_patterns):
            return 'complex'
        
        if any(pattern in question_lower for pattern in simple_patterns):
            return 'simple'
        
        # Long questions = complex
        if word_count > 20:
            return 'complex'
        
        # Multiple questions = complex
        if question.count('?') > 1:
            return 'complex'
        
        # Default: medium
        return 'medium'
    
    def _get_model_config(self, model_name: str) -> Dict[str, str]:
        """Get provider and model config"""
        model_map = {
            'llama-3.3-70b-versatile': {'provider': 'groq', 'model': 'llama-3.3-70b-versatile'},
            'gemini-1.5-flash': {'provider': 'gemini', 'model': 'gemini-1.5-flash'},
            'gpt-4': {'provider': 'openai', 'model': 'gpt-4-turbo-preview'}
        }
        
        return model_map.get(model_name, model_map['llama-3.3-70b-versatile'])
    
    def get_model_info(self, provider: str, model: str) -> Dict[str, Any]:
        """Get information about a model"""
        return self.model_capabilities.get(model, {})


# Global instance
model_router = ModelRouter()

