"""
ALEXA-LIKE FEATURES FOR FRIDAY
Complete voice assistant with timers, routines, lists, and smart automation
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
from loguru import logger


class AlexaFeatures:
    """
    Complete Alexa-like features:
    - Timers and Alarms
    - To-Do Lists
    - Shopping Lists
    - Routines (Morning, Night, Work)
    - Quick Facts
    - Conversational Context
    - Proactive Suggestions
    """
    
    def __init__(self):
        self.data_dir = Path("data/alexa_features")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.timers = []
        self.alarms = []
        self.todo_lists = self._load_json("todo_lists.json", {})
        self.shopping_lists = self._load_json("shopping_lists.json", {})
        self.routines = self._load_json("routines.json", self._default_routines())
        self.context = {}
        
        # Start background timer checker
        self.timer_thread = threading.Thread(target=self._check_timers_loop, daemon=True)
        self.timer_thread.start()
        
        logger.info("Alexa Features initialized (Timers, Lists, Routines)")
    
    def _load_json(self, filename: str, default: Any) -> Any:
        """Load JSON file or return default"""
        filepath = self.data_dir / filename
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading {filename}: {e}")
        return default
    
    def _save_json(self, filename: str, data: Any):
        """Save data to JSON file"""
        filepath = self.data_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Error saving {filename}: {e}")
    
    def _default_routines(self) -> Dict:
        """Default routines like Alexa"""
        return {
            "morning": {
                "name": "Good Morning",
                "enabled": True,
                "actions": [
                    {"type": "greeting", "text": "Good morning! Here's your day ahead."},
                    {"type": "weather", "location": "current"},
                    {"type": "news", "category": "headlines"},
                    {"type": "calendar", "period": "today"},
                    {"type": "todo", "list": "default"}
                ]
            },
            "night": {
                "name": "Good Night",
                "enabled": True,
                "actions": [
                    {"type": "greeting", "text": "Good night! Sleep well."},
                    {"type": "todo", "list": "tomorrow"},
                    {"type": "system", "action": "dim_screen"},
                    {"type": "reminder", "text": "Set alarm for tomorrow"}
                ]
            },
            "work": {
                "name": "Work Mode",
                "enabled": True,
                "actions": [
                    {"type": "greeting", "text": "Let's get to work!"},
                    {"type": "app", "name": "vscode"},
                    {"type": "app", "name": "slack"},
                    {"type": "todo", "list": "work"}
                ]
            },
            "focus": {
                "name": "Focus Mode",
                "enabled": True,
                "actions": [
                    {"type": "greeting", "text": "Focus mode activated. I'll minimize distractions."},
                    {"type": "system", "action": "do_not_disturb"},
                    {"type": "timer", "duration": 25, "name": "Pomodoro"}
                ]
            }
        }
    
    # ============================================
    # TIMERS AND ALARMS
    # ============================================
    
    def set_timer(self, duration: int, name: str = "Timer") -> Dict:
        """
        Set a timer (like Alexa)
        Args:
            duration: Duration in seconds
            name: Timer name
        """
        timer_id = f"timer_{int(time.time())}"
        end_time = time.time() + duration
        
        timer = {
            "id": timer_id,
            "name": name,
            "duration": duration,
            "end_time": end_time,
            "started_at": time.time(),
            "active": True
        }
        
        self.timers.append(timer)
        
        minutes = duration // 60
        seconds = duration % 60
        time_str = f"{minutes} minute{'s' if minutes != 1 else ''}" if minutes > 0 else f"{seconds} seconds"
        
        return {
            "success": True,
            "message": f"Timer set for {time_str}",
            "timer_id": timer_id,
            "ends_at": datetime.fromtimestamp(end_time).strftime("%I:%M %p")
        }
    
    def cancel_timer(self, timer_id: Optional[str] = None) -> Dict:
        """Cancel a timer (or last timer if no ID given)"""
        if not self.timers:
            return {"success": False, "message": "No active timers"}
        
        if timer_id:
            for timer in self.timers:
                if timer["id"] == timer_id:
                    self.timers.remove(timer)
                    return {"success": True, "message": f"Timer '{timer['name']}' cancelled"}
            return {"success": False, "message": "Timer not found"}
        else:
            # Cancel last timer
            timer = self.timers.pop()
            return {"success": True, "message": f"Timer '{timer['name']}' cancelled"}
    
    def get_timers(self) -> Dict:
        """Get all active timers"""
        active_timers = []
        for timer in self.timers:
            remaining = int(timer["end_time"] - time.time())
            if remaining > 0:
                active_timers.append({
                    "id": timer["id"],
                    "name": timer["name"],
                    "remaining_seconds": remaining,
                    "remaining_text": self._format_duration(remaining)
                })
        
        return {
            "success": True,
            "timers": active_timers,
            "count": len(active_timers)
        }
    
    def set_alarm(self, time_str: str, name: str = "Alarm") -> Dict:
        """Set an alarm for specific time"""
        try:
            # Parse time (e.g., "7:30 AM", "19:30")
            alarm_time = self._parse_time(time_str)
            
            alarm_id = f"alarm_{int(time.time())}"
            alarm = {
                "id": alarm_id,
                "name": name,
                "time": alarm_time.strftime("%H:%M"),
                "enabled": True
            }
            
            self.alarms.append(alarm)
            self._save_json("alarms.json", self.alarms)
            
            return {
                "success": True,
                "message": f"Alarm set for {alarm_time.strftime('%I:%M %p')}",
                "alarm_id": alarm_id
            }
        except Exception as e:
            return {"success": False, "message": f"Could not set alarm: {str(e)}"}
    
    def _check_timers_loop(self):
        """Background thread to check timers"""
        while True:
            try:
                current_time = time.time()
                for timer in self.timers[:]:
                    if current_time >= timer["end_time"]:
                        # Timer finished!
                        self.timers.remove(timer)
                        logger.info(f"TIMER FINISHED: {timer['name']}")
                        # Trigger notification (handled by frontend)
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Timer check error: {e}")
                time.sleep(5)
    
    # ============================================
    # TO-DO LISTS
    # ============================================
    
    def add_todo(self, item: str, list_name: str = "default") -> Dict:
        """Add item to to-do list"""
        if list_name not in self.todo_lists:
            self.todo_lists[list_name] = []
        
        todo_item = {
            "id": f"todo_{int(time.time())}",
            "text": item,
            "completed": False,
            "created_at": datetime.now().isoformat()
        }
        
        self.todo_lists[list_name].append(todo_item)
        self._save_json("todo_lists.json", self.todo_lists)
        
        return {
            "success": True,
            "message": f"Added '{item}' to {list_name} list",
            "item": todo_item
        }
    
    def complete_todo(self, item_text: str, list_name: str = "default") -> Dict:
        """Mark todo item as complete"""
        if list_name not in self.todo_lists:
            return {"success": False, "message": f"List '{list_name}' not found"}
        
        for item in self.todo_lists[list_name]:
            if item_text.lower() in item["text"].lower():
                item["completed"] = True
                self._save_json("todo_lists.json", self.todo_lists)
                return {"success": True, "message": f"Marked '{item['text']}' as complete"}
        
        return {"success": False, "message": "Item not found"}
    
    def get_todos(self, list_name: str = "default") -> Dict:
        """Get all items from a to-do list"""
        if list_name not in self.todo_lists:
            return {"success": True, "items": [], "count": 0}
        
        items = self.todo_lists[list_name]
        incomplete = [item for item in items if not item["completed"]]
        
        return {
            "success": True,
            "list_name": list_name,
            "items": incomplete,
            "count": len(incomplete),
            "completed_count": len(items) - len(incomplete)
        }
    
    # ============================================
    # SHOPPING LISTS
    # ============================================
    
    def add_to_shopping_list(self, item: str, quantity: str = "1") -> Dict:
        """Add item to shopping list"""
        if "default" not in self.shopping_lists:
            self.shopping_lists["default"] = []
        
        shopping_item = {
            "id": f"shop_{int(time.time())}",
            "item": item,
            "quantity": quantity,
            "purchased": False,
            "added_at": datetime.now().isoformat()
        }
        
        self.shopping_lists["default"].append(shopping_item)
        self._save_json("shopping_lists.json", self.shopping_lists)
        
        return {
            "success": True,
            "message": f"Added {quantity} {item} to shopping list",
            "item": shopping_item
        }
    
    def get_shopping_list(self) -> Dict:
        """Get shopping list"""
        if "default" not in self.shopping_lists:
            return {"success": True, "items": [], "count": 0}
        
        items = self.shopping_lists["default"]
        unpurchased = [item for item in items if not item["purchased"]]
        
        return {
            "success": True,
            "items": unpurchased,
            "count": len(unpurchased)
        }
    
    # ============================================
    # ROUTINES
    # ============================================
    
    def run_routine(self, routine_name: str) -> Dict:
        """Execute a routine (like Alexa routines)"""
        if routine_name not in self.routines:
            return {"success": False, "message": f"Routine '{routine_name}' not found"}
        
        routine = self.routines[routine_name]
        if not routine["enabled"]:
            return {"success": False, "message": f"Routine '{routine_name}' is disabled"}
        
        results = []
        for action in routine["actions"]:
            result = self._execute_routine_action(action)
            results.append(result)
        
        return {
            "success": True,
            "routine": routine_name,
            "actions_executed": len(results),
            "results": results
        }
    
    def _execute_routine_action(self, action: Dict) -> Dict:
        """Execute a single routine action"""
        action_type = action.get("type")
        
        if action_type == "greeting":
            return {"type": "speak", "text": action.get("text", "")}
        elif action_type == "timer":
            return self.set_timer(action.get("duration", 300) * 60, action.get("name", "Timer"))
        elif action_type == "todo":
            return self.get_todos(action.get("list", "default"))
        else:
            return {"type": action_type, "data": action}
    
    # ============================================
    # QUICK FACTS AND CALCULATIONS
    # ============================================
    
    def quick_answer(self, query: str) -> Optional[str]:
        """
        Quick answers for simple questions (like Alexa)
        Returns answer if it's a simple query, None if needs AI
        """
        query_lower = query.lower()
        
        # Time
        if any(word in query_lower for word in ["what time", "current time", "time is it"]):
            return f"It's {datetime.now().strftime('%I:%M %p')}"
        
        # Date
        if any(word in query_lower for word in ["what date", "today's date", "what day"]):
            return datetime.now().strftime("%A, %B %d, %Y")
        
        # Simple calculations
        if any(word in query_lower for word in ["what is", "calculate", "plus", "minus", "times", "divided"]):
            try:
                # Extract numbers and operators
                import re
                calc = re.sub(r'[^0-9+\-*/().]', '', query_lower.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/"))
                if calc:
                    result = eval(calc)
                    return f"The answer is {result}"
            except:
                pass
        
        return None  # Let AI handle it
    
    # ============================================
    # CONVERSATIONAL CONTEXT
    # ============================================
    
    def set_context(self, key: str, value: Any):
        """Set conversational context"""
        self.context[key] = value
    
    def get_context(self, key: str) -> Any:
        """Get conversational context"""
        return self.context.get(key)
    
    def clear_context(self):
        """Clear conversational context"""
        self.context = {}
    
    # ============================================
    # PROACTIVE SUGGESTIONS
    # ============================================
    
    def get_proactive_suggestion(self) -> Optional[str]:
        """
        Get proactive suggestions based on time and context
        (Like Alexa's hunches and suggestions)
        """
        current_hour = datetime.now().hour
        
        # Morning suggestions (6 AM - 10 AM)
        if 6 <= current_hour < 10:
            if "morning_routine_done" not in self.context:
                return "Good morning! Would you like me to run your morning routine?"
        
        # Work time suggestions (9 AM - 5 PM)
        elif 9 <= current_hour < 17:
            todos = self.get_todos("work")
            if todos["count"] > 0:
                return f"You have {todos['count']} work tasks pending. Would you like to hear them?"
        
        # Evening suggestions (6 PM - 9 PM)
        elif 18 <= current_hour < 21:
            return "It's evening. Would you like me to play some relaxing music?"
        
        # Night suggestions (9 PM - midnight)
        elif 21 <= current_hour < 24:
            if "night_routine_done" not in self.context:
                return "It's getting late. Would you like me to run your night routine?"
        
        return None
    
    # ============================================
    # UTILITIES
    # ============================================
    
    def _format_duration(self, seconds: int) -> str:
        """Format seconds to human-readable duration"""
        if seconds < 60:
            return f"{seconds} seconds"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''} {secs} seconds"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours} hour{'s' if hours != 1 else ''} {mins} minutes"
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime"""
        # Try different formats
        formats = ["%I:%M %p", "%H:%M", "%I %p"]
        for fmt in formats:
            try:
                time_obj = datetime.strptime(time_str, fmt)
                # Combine with today's date
                now = datetime.now()
                alarm_time = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                # If time has passed today, set for tomorrow
                if alarm_time < now:
                    alarm_time += timedelta(days=1)
                return alarm_time
            except:
                continue
        raise ValueError(f"Could not parse time: {time_str}")


# Global instance
alexa_features = AlexaFeatures()

