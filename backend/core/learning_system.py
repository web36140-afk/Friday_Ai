"""
Self-Learning System
Learn from user interactions, adapt behavior, remember preferences
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
from loguru import logger


class LearningSystem:
    """Self-learning system that adapts to user behavior"""
    
    def __init__(self):
        self.data_dir = Path("../data/learning")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.preferences_file = self.data_dir / "user_preferences.json"
        self.commands_file = self.data_dir / "command_patterns.json"
        self.feedback_file = self.data_dir / "feedback_log.json"
        
        self.user_preferences: Dict[str, Any] = {}
        self.command_patterns: Dict[str, Any] = {}
        self.feedback_log: List[Dict] = []
        
        self.load_data()
    
    def load_data(self):
        """Load learning data from disk"""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            
            if self.commands_file.exists():
                with open(self.commands_file, 'r', encoding='utf-8') as f:
                    self.command_patterns = json.load(f)
            
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_log = json.load(f)
            
            logger.info(f"Learning system loaded: {len(self.user_preferences)} preferences")
        except Exception as e:
            logger.error(f"Failed to load learning data: {e}")
    
    def save_data(self):
        """Save learning data to disk"""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=2)
            
            with open(self.commands_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_patterns, f, indent=2)
            
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_log[-1000:], f, indent=2)  # Keep last 1000
            
            logger.debug("Learning data saved")
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")
    
    def learn_from_interaction(
        self,
        user_message: str,
        ai_response: str,
        language: str,
        tools_used: List[str] = None,
        response_time: float = 0.0
    ):
        """Learn from a user interaction"""
        # Track language preference
        if "language_preference" not in self.user_preferences:
            self.user_preferences["language_preference"] = Counter()
        
        lang_key = language or "en-US"
        if isinstance(self.user_preferences["language_preference"], dict):
            self.user_preferences["language_preference"][lang_key] = \
                self.user_preferences["language_preference"].get(lang_key, 0) + 1
        
        # Track common commands
        if "common_commands" not in self.command_patterns:
            self.command_patterns["common_commands"] = []
        
        # Extract command pattern (first few words)
        command_start = " ".join(user_message.lower().split()[:3])
        self.command_patterns["common_commands"].append({
            "pattern": command_start,
            "timestamp": datetime.now().isoformat(),
            "tools_used": tools_used or [],
            "response_time": response_time
        })
        
        # Keep only last 500 commands
        if len(self.command_patterns["common_commands"]) > 500:
            self.command_patterns["common_commands"] = \
                self.command_patterns["common_commands"][-500:]
        
        # Track tool usage
        if tools_used:
            if "tool_usage" not in self.user_preferences:
                self.user_preferences["tool_usage"] = Counter()
            
            for tool in tools_used:
                if isinstance(self.user_preferences["tool_usage"], dict):
                    self.user_preferences["tool_usage"][tool] = \
                        self.user_preferences["tool_usage"].get(tool, 0) + 1
        
        # Track interaction time
        hour = datetime.now().hour
        if "active_hours" not in self.user_preferences:
            self.user_preferences["active_hours"] = Counter()
        
        if isinstance(self.user_preferences["active_hours"], dict):
            self.user_preferences["active_hours"][str(hour)] = \
                self.user_preferences["active_hours"].get(str(hour), 0) + 1
        
        self.save_data()
    
    def learn_preference(self, preference_key: str, preference_value: Any):
        """Learn a specific user preference"""
        self.user_preferences[preference_key] = preference_value
        self.save_data()
        logger.info(f"Learned preference: {preference_key} = {preference_value}")
    
    def get_preference(self, preference_key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.user_preferences.get(preference_key, default)
    
    def record_feedback(
        self,
        interaction_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None
    ):
        """Record user feedback"""
        feedback = {
            "interaction_id": interaction_id,
            "feedback_type": feedback_type,  # positive, negative, neutral
            "rating": rating,  # 1-5
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_log.append(feedback)
        self.save_data()
        logger.info(f"Feedback recorded: {feedback_type}")
    
    def get_most_used_commands(self, limit: int = 10) -> List[Dict]:
        """Get most frequently used commands"""
        commands = self.command_patterns.get("common_commands", [])
        
        # Count patterns
        pattern_counts = Counter()
        for cmd in commands:
            pattern_counts[cmd["pattern"]] += 1
        
        # Get top patterns
        top_patterns = []
        for pattern, count in pattern_counts.most_common(limit):
            top_patterns.append({
                "pattern": pattern,
                "count": count
            })
        
        return top_patterns
    
    def get_preferred_language(self) -> str:
        """Get user's preferred language"""
        lang_prefs = self.user_preferences.get("language_preference", {})
        
        if not lang_prefs:
            return "en-US"
        
        # Convert Counter to dict if needed
        if not isinstance(lang_prefs, dict):
            lang_prefs = dict(lang_prefs)
        
        # Get most used language
        most_used = max(lang_prefs.items(), key=lambda x: x[1])
        return most_used[0]
    
    def get_active_hours(self) -> List[int]:
        """Get user's most active hours"""
        hours = self.user_preferences.get("active_hours", {})
        
        if not hours:
            return []
        
        # Convert Counter to dict if needed
        if not isinstance(hours, dict):
            hours = dict(hours)
        
        # Get top 5 active hours
        sorted_hours = sorted(hours.items(), key=lambda x: x[1], reverse=True)
        return [int(h[0]) for h in sorted_hours[:5]]
    
    def suggest_response_style(self, context: str) -> Dict[str, Any]:
        """Suggest response style based on learned patterns"""
        # Analyze most common feedback
        positive_count = sum(1 for f in self.feedback_log if f["feedback_type"] == "positive")
        negative_count = sum(1 for f in self.feedback_log if f["feedback_type"] == "negative")
        
        # Default style
        style = {
            "verbosity": "medium",  # low, medium, high
            "formality": "friendly",  # formal, friendly, casual
            "include_examples": True,
            "use_emojis": False
        }
        
        # Adjust based on feedback
        if positive_count > negative_count * 2:
            style["confidence"] = "high"
        elif negative_count > positive_count:
            style["confidence"] = "medium"
            style["verbosity"] = "high"  # Be more explanatory
        
        return style
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        return {
            "total_preferences": len(self.user_preferences),
            "total_commands_learned": len(self.command_patterns.get("common_commands", [])),
            "total_feedback": len(self.feedback_log),
            "preferred_language": self.get_preferred_language(),
            "most_used_commands": self.get_most_used_commands(5),
            "active_hours": self.get_active_hours(),
            "positive_feedback": sum(1 for f in self.feedback_log if f["feedback_type"] == "positive"),
            "negative_feedback": sum(1 for f in self.feedback_log if f["feedback_type"] == "negative")
        }


# Global instance
learning_system = LearningSystem()

