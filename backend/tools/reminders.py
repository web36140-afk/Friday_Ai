"""
Reminders & Schedule Tool
Set reminders, schedule tasks, create to-do lists
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

from core.tool_manager import BaseTool


class RemindersScheduleTool(BaseTool):
    """Manage reminders, schedules, and to-do lists"""
    
    name = "reminders"
    description = "Set reminders, schedule tasks, manage to-do lists"
    
    def __init__(self):
        super().__init__()
        self.data_dir = Path("../data/reminders")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reminders_file = self.data_dir / "reminders.json"
        self.reminders: List[Dict] = []
        self._load_reminders()
    
    def _load_reminders(self):
        """Load reminders from disk"""
        if self.reminders_file.exists():
            try:
                with open(self.reminders_file, 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
                logger.debug(f"Loaded {len(self.reminders)} reminders")
            except Exception as e:
                logger.error(f"Failed to load reminders: {e}")
                self.reminders = []
    
    def _save_reminders(self):
        """Save reminders to disk"""
        try:
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, indent=2)
            logger.debug("Reminders saved")
        except Exception as e:
            logger.error(f"Failed to save reminders: {e}")
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute reminder operation"""
        operations = {
            "add": self.add_reminder,
            "list": self.list_reminders,
            "delete": self.delete_reminder,
            "complete": self.mark_complete,
            "update": self.update_reminder,
            "check_due": self.check_due_reminders
        }
        
        if operation not in operations:
            return {
                "error": f"Unknown operation: {operation}",
                "available": list(operations.keys())
            }
        
        try:
            result = await operations[operation](**kwargs)
            return result
        except Exception as e:
            logger.error(f"Reminder operation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }
    
    async def add_reminder(
        self,
        title: str,
        description: str = "",
        due_date: str = None,
        priority: str = "medium",
        category: str = "general"
    ) -> Dict[str, Any]:
        """Add a new reminder"""
        reminder = {
            "id": len(self.reminders) + 1,
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,  # low, medium, high
            "category": category,
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.reminders.append(reminder)
        self._save_reminders()
        
        return {
            "success": True,
            "operation": "add_reminder",
            "reminder": reminder,
            "message": f"Reminder '{title}' added successfully"
        }
    
    async def list_reminders(
        self,
        status: str = "all",
        category: str = None,
        priority: str = None
    ) -> Dict[str, Any]:
        """List reminders with filters"""
        filtered = self.reminders.copy()
        
        # Filter by status
        if status == "active":
            filtered = [r for r in filtered if not r["completed"]]
        elif status == "completed":
            filtered = [r for r in filtered if r["completed"]]
        
        # Filter by category
        if category:
            filtered = [r for r in filtered if r["category"] == category]
        
        # Filter by priority
        if priority:
            filtered = [r for r in filtered if r["priority"] == priority]
        
        # Sort by priority and due date
        def sort_key(r):
            priority_order = {"high": 0, "medium": 1, "low": 2}
            return (
                r["completed"],
                priority_order.get(r["priority"], 99),
                r["due_date"] or "9999-99-99"
            )
        
        filtered.sort(key=sort_key)
        
        return {
            "success": True,
            "operation": "list_reminders",
            "total": len(filtered),
            "reminders": filtered
        }
    
    async def delete_reminder(self, reminder_id: int) -> Dict[str, Any]:
        """Delete a reminder"""
        original_count = len(self.reminders)
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
        
        if len(self.reminders) < original_count:
            self._save_reminders()
            return {
                "success": True,
                "operation": "delete_reminder",
                "message": f"Reminder {reminder_id} deleted"
            }
        else:
            return {
                "success": False,
                "error": f"Reminder {reminder_id} not found"
            }
    
    async def mark_complete(self, reminder_id: int) -> Dict[str, Any]:
        """Mark reminder as complete"""
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["completed"] = True
                reminder["updated_at"] = datetime.now().isoformat()
                self._save_reminders()
                return {
                    "success": True,
                    "operation": "mark_complete",
                    "reminder": reminder,
                    "message": f"Reminder '{reminder['title']}' marked as complete"
                }
        
        return {
            "success": False,
            "error": f"Reminder {reminder_id} not found"
        }
    
    async def update_reminder(
        self,
        reminder_id: int,
        **updates
    ) -> Dict[str, Any]:
        """Update reminder fields"""
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                for key, value in updates.items():
                    if key in reminder:
                        reminder[key] = value
                reminder["updated_at"] = datetime.now().isoformat()
                self._save_reminders()
                return {
                    "success": True,
                    "operation": "update_reminder",
                    "reminder": reminder
                }
        
        return {
            "success": False,
            "error": f"Reminder {reminder_id} not found"
        }
    
    async def check_due_reminders(self) -> Dict[str, Any]:
        """Check for due/overdue reminders"""
        now = datetime.now()
        due_soon = []
        overdue = []
        
        for reminder in self.reminders:
            if reminder["completed"]:
                continue
            
            if not reminder["due_date"]:
                continue
            
            try:
                due_date = datetime.fromisoformat(reminder["due_date"])
                
                if due_date < now:
                    overdue.append(reminder)
                elif due_date < now + timedelta(hours=24):
                    due_soon.append(reminder)
            except:
                pass
        
        return {
            "success": True,
            "operation": "check_due_reminders",
            "overdue": overdue,
            "due_soon": due_soon,
            "total_overdue": len(overdue),
            "total_due_soon": len(due_soon)
        }
    
    def validate_args(self, operation: str = None, **kwargs) -> bool:
        """Validate arguments"""
        return bool(operation)

