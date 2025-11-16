"""
Voice Command Helper
Provides utility functions for voice command processing
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from difflib import SequenceMatcher


class VoiceCommandHelper:
    """Helper functions for voice command processing"""
    
    def __init__(self):
        # Common variations of commands
        self.command_synonyms = {
            "open": ["launch", "start", "run", "execute", "load", "show"],
            "close": ["exit", "quit", "terminate", "kill", "stop"],
            "search": ["find", "look for", "locate", "google"],
            "go to": ["visit", "browse", "navigate to", "open website"],
            "maximize": ["full screen", "make bigger", "expand"],
            "minimize": ["make smaller", "shrink", "reduce"],
        }
        
        # Filler words to remove for better matching
        self.filler_words = [
            "please", "can you", "could you", "would you",
            "i want to", "i need to", "i'd like to",
            "hey", "hi", "hello", "ok", "okay",
            "the", "a", "an", "my", "for me"
        ]
        
        logger.info("🎙️ Voice Command Helper initialized")
    
    def clean_command(self, command: str) -> str:
        """
        Clean voice command by removing filler words and normalizing
        
        Example:
            "Hey FRIDAY please open the calculator for me"
            → "open calculator"
        """
        command = command.lower().strip()
        
        # Remove wake word if present
        wake_words = ["friday", "hey friday", "ok friday"]
        for wake in wake_words:
            command = command.replace(wake, "").strip()
        
        # Remove filler words
        for filler in self.filler_words:
            command = re.sub(rf'\b{filler}\b', '', command, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        command = ' '.join(command.split())
        
        return command
    
    def expand_synonyms(self, command: str) -> List[str]:
        """
        Generate command variations using synonyms
        
        Example:
            "open chrome" → ["open chrome", "launch chrome", "start chrome", ...]
        """
        variations = [command]
        
        for base_word, synonyms in self.command_synonyms.items():
            if base_word in command:
                for synonym in synonyms:
                    variations.append(command.replace(base_word, synonym))
        
        return variations
    
    def fuzzy_match_app(self, input_name: str, app_list: List[str], threshold: float = 0.7) -> Optional[str]:
        """
        Fuzzy match app name to handle slight mispronunciations
        
        Example:
            "visual studio" → "vscode"
            "power point" → "powerpoint"
        """
        input_name = input_name.lower().strip()
        
        best_match = None
        best_ratio = 0
        
        for app in app_list:
            ratio = SequenceMatcher(None, input_name, app.lower()).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = app
        
        if best_ratio >= threshold:
            logger.info(f"🎯 Fuzzy matched '{input_name}' to '{best_match}' (score: {best_ratio:.2f})")
            return best_match
        
        return None
    
    def extract_chain_commands(self, command: str) -> List[str]:
        """
        Extract chained commands separated by 'and then', 'then', 'and', 'after that'
        
        Example:
            "open chrome and then go to youtube"
            → ["open chrome", "go to youtube"]
        """
        # Split patterns
        patterns = [
            r'\s+and\s+then\s+',
            r'\s+then\s+',
            r'\s+after\s+that\s+',
            r'\s+followed\s+by\s+',
        ]
        
        parts = [command]
        for pattern in patterns:
            new_parts = []
            for part in parts:
                new_parts.extend(re.split(pattern, part))
            parts = new_parts
        
        # Also split by " and " if it connects actions (not objects)
        final_parts = []
        for part in parts:
            # Only split if "and" connects verbs, not nouns
            if ' and ' in part:
                words = part.split(' and ')
                # If both sides have action verbs, split
                action_verbs = ['open', 'close', 'launch', 'go', 'visit', 'show', 'search']
                if any(verb in words[0] for verb in action_verbs) and any(verb in words[1] for verb in action_verbs):
                    final_parts.extend(words)
                else:
                    final_parts.append(part)
            else:
                final_parts.append(part)
        
        # Clean each part
        cleaned = [self.clean_command(part) for part in final_parts]
        
        # Remove empty strings
        cleaned = [c for c in cleaned if c]
        
        logger.info(f"📋 Extracted {len(cleaned)} chained commands: {cleaned}")
        
        return cleaned
    
    def is_question(self, command: str) -> bool:
        """
        Determine if command is a question (for AI) vs action command
        
        Questions → Send to AI chat
        Actions → Execute directly
        """
        question_words = [
            "what", "when", "where", "why", "how", "who",
            "is", "are", "can", "could", "would", "should",
            "do", "does", "did"
        ]
        
        command_lower = command.lower().strip()
        
        # Starts with question word
        if any(command_lower.startswith(q) for q in question_words):
            return True
        
        # Ends with question mark
        if command.endswith('?'):
            return True
        
        # Contains question patterns
        question_patterns = [
            r'\bwhat is\b', r'\bwhere is\b', r'\bhow do\b',
            r'\bcan you tell\b', r'\bdo you know\b',
            r'\bexplain\b', r'\btell me\b'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, command_lower):
                return True
        
        return False
    
    def extract_target(self, command: str, action: str) -> Optional[str]:
        """
        Extract target from command after action word
        
        Example:
            "open calculator" with action="open" → "calculator"
            "go to youtube" with action="go to" → "youtube"
        """
        command_lower = command.lower()
        
        # Find action in command
        action_pos = command_lower.find(action)
        if action_pos == -1:
            return None
        
        # Extract everything after action
        target = command[action_pos + len(action):].strip()
        
        # Remove common trailing words
        trailing_words = ["please", "now", "right now", "immediately"]
        for trailing in trailing_words:
            target = re.sub(rf'\s+{trailing}$', '', target, flags=re.IGNORECASE)
        
        return target.strip() if target else None
    
    def detect_intent(self, command: str) -> Dict[str, Any]:
        """
        Detect intent of voice command
        
        Returns:
            {
                "intent": "open_app" | "open_website" | "system_control" | "question" | "unknown",
                "action": str,
                "target": str,
                "confidence": float
            }
        """
        command_clean = self.clean_command(command)
        
        # Check if it's a question
        if self.is_question(command):
            return {
                "intent": "question",
                "action": "ask",
                "target": command_clean,
                "confidence": 0.9
            }
        
        # Detect action
        action_patterns = {
            "open_app": [r'\b(open|launch|start|run)\s+(.+)'],
            "open_website": [r'\b(go to|visit|browse|open website)\s+(.+)'],
            "search": [r'\b(search|find|google|look for)\s+(.+)'],
            "system_control": [
                r'\b(shutdown|restart|sleep|lock|hibernate)\b',
                r'\b(maximize|minimize|close)\s+(window|this)?\b',
                r'\b(show|hide)\s+desktop\b',
                r'\b(mute|unmute|volume)\b'
            ],
            "file_operation": [
                r'\b(show me|access|open file|open folder)\s+(.+)'
            ]
        }
        
        for intent, patterns in action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command_clean, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    action = groups[0] if groups else ""
                    target = groups[1] if len(groups) > 1 else ""
                    
                    return {
                        "intent": intent,
                        "action": action,
                        "target": target.strip(),
                        "confidence": 0.85
                    }
        
        return {
            "intent": "unknown",
            "action": "",
            "target": command_clean,
            "confidence": 0.3
        }
    
    def normalize_app_name(self, app_name: str) -> str:
        """
        Normalize app names for better matching
        
        Examples:
            "visual studio code" → "vscode"
            "microsoft word" → "word"
            "google chrome" → "chrome"
        """
        normalizations = {
            "visual studio code": "vscode",
            "vs code": "vscode",
            "microsoft word": "word",
            "microsoft excel": "excel",
            "microsoft powerpoint": "powerpoint",
            "google chrome": "chrome",
            "mozilla firefox": "firefox",
            "microsoft edge": "edge",
            "notepad plus plus": "notepad++",
            "command prompt": "cmd",
            "task manager": "taskmgr",
        }
        
        app_lower = app_name.lower().strip()
        return normalizations.get(app_lower, app_lower)
    
    def suggest_corrections(self, failed_command: str, available_commands: List[str]) -> List[Tuple[str, float]]:
        """
        Suggest corrections for failed commands
        
        Returns list of (command, similarity_score) tuples
        """
        suggestions = []
        
        for available_cmd in available_commands:
            ratio = SequenceMatcher(None, failed_command.lower(), available_cmd.lower()).ratio()
            if ratio > 0.5:  # At least 50% similar
                suggestions.append((available_cmd, ratio))
        
        # Sort by similarity score (descending)
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:5]  # Top 5 suggestions
    
    def validate_command_safety(self, command: str) -> Dict[str, Any]:
        """
        Validate if command is safe to execute
        
        Checks for potentially dangerous operations
        """
        dangerous_patterns = [
            r'\bdel\b',
            r'\bformat\b',
            r'\brmdir\b',
            r'\brm\s+-rf\b',
            r'\bdestroy\b',
            r'\bwipe\b',
            r'system32',
        ]
        
        command_lower = command.lower()
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return {
                    "safe": False,
                    "reason": f"Command contains potentially dangerous operation: {pattern}",
                    "requires_confirmation": True
                }
        
        return {
            "safe": True,
            "reason": "Command appears safe",
            "requires_confirmation": False
        }


# Global instance
voice_helper = VoiceCommandHelper()

