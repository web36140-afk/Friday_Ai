"""
Gesture Control API
Handle hand tracking gesture commands
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger

from core.tool_manager import tool_manager

router = APIRouter()


class GestureCommand(BaseModel):
    """Gesture command model"""
    gesture: str
    params: Optional[Dict[str, Any]] = {}


@router.post("/gesture/execute")
async def execute_gesture_command(command: GestureCommand):
    """Execute a gesture command"""
    try:
        logger.info(f"🖐️ Gesture command: {command.gesture}")
        
        # Map gestures to tool operations
        gesture_map = {
            # Music Control
            "music_toggle": ("media_control", "play_pause", {}),
            "music_next": ("media_control", "next_track", {}),
            "music_previous": ("media_control", "previous_track", {}),
            "music_stop": ("media_control", "stop", {}),
            
            # Volume Control
            "volume_up": ("windows_control", "volume_up", {"step": 10}),
            "volume_down": ("windows_control", "volume_down", {"step": 10}),
            "volume_set": ("windows_control", "volume_set", command.params),
            "volume_mute": ("windows_control", "volume_mute", {}),
            
            # System Control (Power management)
            "lock_pc": ("windows_control", "lock", {}),
            "sleep_pc": ("windows_control", "sleep", {}),
            "shutdown_pc": ("windows_control", "shutdown", {"delay": 30}),
            "restart_pc": ("windows_control", "restart", {"delay": 30}),
            
            # App Control
            "open_app": ("windows_control", "open_app", command.params),
            "close_app": ("windows_control", "close_app", command.params),
            
            # Mouse/Keyboard
            "mouse_click": ("os_automation", "mouse_click", command.params),
            "mouse_move": ("os_automation", "mouse_move", command.params),
            "keyboard_input": ("os_automation", "keyboard", command.params),
        }
        
        if command.gesture not in gesture_map:
            return {
                "success": False,
                "error": f"Unknown gesture: {command.gesture}",
                "available": list(gesture_map.keys())
            }
        
        tool_name, operation, params = gesture_map[command.gesture]
        
        # Execute via tool manager
        result = await tool_manager.execute_tool(
            tool_name,
            operation=operation,
            **params
        )
        
        return {
            "success": True,
            "gesture": command.gesture,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Gesture command error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gesture/capabilities")
async def get_gesture_capabilities():
    """Get available gesture commands"""
    return {
        "music_control": [
            "music_toggle",
            "music_next",
            "music_previous",
            "music_stop"
        ],
        "volume_control": [
            "volume_up",
            "volume_down",
            "volume_set",
            "volume_mute"
        ],
        "system_control": [
            "lock_pc",
            "sleep_pc"
        ],
        "app_control": [
            "open_app",
            "close_app"
        ],
        "input_control": [
            "mouse_click",
            "mouse_move",
            "keyboard_input"
        ]
    }

