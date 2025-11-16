"""
Chain of Thought Reasoning Engine
Enhances AI responses with step-by-step reasoning
"""
from typing import List, Dict, Any
from loguru import logger


class ReasoningEngine:
    """
    Implements Chain of Thought (CoT) reasoning for complex questions
    Makes FRIDAY think step-by-step like GPT-4
    """
    
    def should_use_cot(self, question: str, context: Dict[str, Any]) -> bool:
        """
        Determine if question requires Chain of Thought reasoning
        """
        question_lower = question.lower()
        
        # Complex question indicators
        cot_triggers = [
            'why', 'how', 'explain', 'reason', 'cause',
            'compare', 'difference', 'vs', 'better',
            'solve', 'calculate', 'analyze', 'evaluate',
            'pros and cons', 'advantages', 'disadvantages'
        ]
        
        # Check if question is complex
        if any(trigger in question_lower for trigger in cot_triggers):
            return True
        
        # Long questions often need reasoning
        if len(question.split()) > 10:
            return True
        
        # Multi-part questions
        if '?' in question and question.count('?') > 1:
            return True
        
        return False
    
    def build_cot_prompt(self, question: str, context: Dict[str, Any]) -> str:
        """
        Build a Chain of Thought prompt for the LLM
        """
        intent = context.get('intent', 'question')
        topic = context.get('current_topic')
        
        cot_templates = {
            'comparison': """
Let's compare step by step:
1. First, identify the key aspects to compare
2. Analyze each option's strengths and weaknesses
3. Consider the context and requirements
4. Provide a reasoned conclusion

Now answer: {question}
""",
            'explanation_seeking': """
Let's break this down logically:
1. What is the core concept?
2. What are the underlying principles?
3. How does it work in practice?
4. Why is this important?

Now explain: {question}
""",
            'instruction_seeking': """
Let's think through this step by step:
1. What is the goal?
2. What are the prerequisites?
3. What are the steps to achieve it?
4. What are potential issues to watch for?

Now provide guidance for: {question}
""",
            'problem_solving': """
Let's solve this systematically:
1. Understand the problem
2. Identify known information
3. Determine what we need to find
4. Apply appropriate methods
5. Verify the solution

Now address: {question}
"""
        }
        
        # Select appropriate template
        if 'compare' in question.lower() or 'vs' in question.lower():
            template = cot_templates['comparison']
        elif intent == 'explanation_seeking':
            template = cot_templates['explanation_seeking']
        elif intent == 'instruction_seeking':
            template = cot_templates['instruction_seeking']
        elif any(word in question.lower() for word in ['solve', 'calculate', 'find']):
            template = cot_templates['problem_solving']
        else:
            template = cot_templates['explanation_seeking']  # Default
        
        return template.format(question=question)
    
    def enhance_with_reasoning(self, prompt: str, question: str, context: Dict[str, Any]) -> str:
        """
        Enhance the prompt with reasoning instructions
        """
        if self.should_use_cot(question, context):
            cot_addition = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓 REASONING MODE ACTIVATED (Chain of Thought)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This question requires step-by-step reasoning. Think through it logically:

{self.build_cot_prompt(question, context)}

Provide a well-reasoned, structured answer.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            return prompt + "\n" + cot_addition
        
        return prompt


# Global instance
reasoning_engine = ReasoningEngine()

