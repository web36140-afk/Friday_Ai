"""
Ultra Gesture Control API
Connects frontend hand tracking to desktop automation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger

router = APIRouter(prefix="/api/gesture", tags=["gesture"])


# ============================================
# REQUEST MODELS
# ============================================

class CursorUpdate(BaseModel):
    x: float  # 0-1 normalized
    y: float  # 0-1 normalized
    smooth: bool = True


class ClickRequest(BaseModel):
    button: str = "left"  # left, right, middle
    clicks: int = 1


class DragRequest(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None


class SwipeRequest(BaseModel):
    direction: str  # up, down, left, right


class WindowAction(BaseModel):
    action: str  # maximize, minimize, close, snap_left, snap_right


class AppLaunchRequest(BaseModel):
    app_name: str


class GestureSettings(BaseModel):
    cursor_smoothing: Optional[float] = None
    cursor_speed: Optional[float] = None
    pinch_threshold: Optional[float] = None


# ============================================
# ENDPOINTS
# ============================================

@router.post("/cursor")
async def update_cursor(request: CursorUpdate):
    """Update cursor position from hand tracking"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        result = await tool_instance.move_cursor(
            x=request.x,
            y=request.y,
            smooth=request.smooth
        )
        
        return {"success": True, "position": result}
        
    except Exception as e:
        logger.error(f"Cursor update error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/click")
async def perform_click(request: ClickRequest):
    """Execute mouse click"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        result = await tool_instance.perform_click(
            button=request.button,
            clicks=request.clicks
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Click error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/double-click")
async def double_click():
    """Execute double click"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.perform_double_click()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/right-click")
async def right_click():
    """Execute right click"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.perform_right_click()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/drag-start")
async def drag_start(request: DragRequest):
    """Start drag operation"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        result = await tool_instance.start_drag(
            x=request.x,
            y=request.y
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/drag-move")
async def drag_move(request: DragRequest):
    """Continue drag operation"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        result = await tool_instance.continue_drag(
            x=request.x,
            y=request.y
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/drag-end")
async def drag_end():
    """End drag operation"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.end_drag()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/swipe")
async def handle_swipe(request: SwipeRequest):
    """Handle swipe gesture"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        result = await tool_instance.three_finger_swipe(direction=request.direction)
        
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/window")
async def window_action(request: WindowAction):
    """Perform window management action"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        actions = {
            "maximize": tool_instance.maximize_active_window,
            "minimize": tool_instance.minimize_active_window,
            "close": tool_instance.close_active_window,
            "snap_left": tool_instance.snap_window_left,
            "snap_right": tool_instance.snap_window_right,
            "show_desktop": tool_instance.show_desktop
        }
        
        if request.action not in actions:
            return {"success": False, "error": f"Unknown action: {request.action}"}
        
        result = await actions[request.action]()
        
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/scroll")
async def handle_scroll(direction: str = "down", amount: int = 3):
    """Scroll up or down"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.perform_scroll(direction=direction, amount=amount)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/zoom")
async def handle_zoom(direction: str = "in"):
    """Zoom in or out"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.perform_zoom(direction=direction)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/launch-app")
async def launch_app(request: AppLaunchRequest):
    """Launch application"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.launch_application(app_name=request.app_name)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/monitors")
async def get_monitors():
    """Get monitor information"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.get_monitor_info()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/settings")
async def get_settings():
    """Get current gesture control settings"""
    try:
        from tools.advanced_gesture_control import tool_instance
        result = await tool_instance.get_current_settings()
        return {"success": True, "settings": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/settings")
async def update_settings(settings: GestureSettings):
    """Update gesture control settings"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        settings_dict = settings.dict(exclude_unset=True)
        result = await tool_instance.update_settings(**settings_dict)
        
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/calibrate")
async def calibrate(smoothing: Optional[float] = None, speed: Optional[float] = None):
    """Calibrate gesture tracking"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        result = await tool_instance.calibrate_tracking(
            smoothing=smoothing,
            speed=speed
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/status")
async def get_status():
    """Get gesture control system status"""
    try:
        from tools.advanced_gesture_control import tool_instance
        
        settings = await tool_instance.get_current_settings()
        
        return {
            "success": True,
            "status": "online",
            "settings": settings,
            "features": [
                "Cursor Control",
                "Click & Drag",
                "Window Management",
                "Multi-Monitor",
                "Advanced Gestures",
                "Calibration"
            ]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


logger.info("🖐️ Ultra Gesture Control API loaded")

