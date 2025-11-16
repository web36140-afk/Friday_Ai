"""
ADVANCED OPENCV GESTURE API
Professional finger tracking with continuous detection
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

router = APIRouter()


class GestureStartRequest(BaseModel):
    camera_index: Optional[int] = 0
    auto_brightness: Optional[bool] = True


class GestureCommandRequest(BaseModel):
    command: str  # start, stop, status, cursor_move, click, etc.
    params: Optional[Dict[str, Any]] = {}


# Global gesture instance (lazy loaded)
_gesture_instance = None


def get_gesture_instance():
    """Get or create gesture tracking instance"""
    global _gesture_instance
    if _gesture_instance is None:
        from tools.advanced_opencv_gesture import advanced_gesture
        _gesture_instance = advanced_gesture
    return _gesture_instance


@router.post("/api/opencv-gesture/start")
async def start_gesture_tracking(request: GestureStartRequest):
    """Start advanced OpenCV gesture tracking"""
    try:
        gesture = get_gesture_instance()
        
        # Configure settings
        gesture.auto_brightness = request.auto_brightness
        
        # Start camera
        success = gesture.start_camera()
        
        if success:
            return {
                "success": True,
                "message": "Gesture tracking started",
                "status": gesture.get_status()
            }
        else:
            return {
                "success": False,
                "message": "Failed to start camera"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/opencv-gesture/stop")
async def stop_gesture_tracking():
    """Stop gesture tracking"""
    try:
        gesture = get_gesture_instance()
        gesture.stop()
        
        return {
            "success": True,
            "message": "Gesture tracking stopped"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/opencv-gesture/status")
async def get_gesture_status():
    """Get current gesture tracking status"""
    try:
        gesture = get_gesture_instance()
        status = gesture.get_status()
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/opencv-gesture/process")
async def process_gesture_frame():
    """Process a single frame and get hand data"""
    try:
        gesture = get_gesture_instance()
        result = gesture.process_frame()
        
        if result:
            # Execute gesture actions
            gesture.execute_gesture(result['gesture'])
            
            # Move cursor based on index finger
            if result['landmarks'].get('index_tip'):
                x, y, _ = result['landmarks']['index_tip']
                gesture.move_cursor(x, y, smooth=True)
            
            return {
                "success": True,
                "hand_detected": True,
                "gesture": result['gesture'],
                "handedness": result['handedness']
            }
        else:
            return {
                "success": True,
                "hand_detected": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/opencv-gesture/settings")
async def update_gesture_settings(settings: Dict[str, Any]):
    """Update gesture tracking settings"""
    try:
        gesture = get_gesture_instance()
        
        # Update settings
        if 'cursor_smoothing' in settings:
            gesture.cursor_smoothing = float(settings['cursor_smoothing'])
        
        if 'pinch_threshold' in settings:
            gesture.pinch_threshold = float(settings['pinch_threshold'])
        
        if 'grab_threshold' in settings:
            gesture.grab_threshold = float(settings['grab_threshold'])
        
        if 'auto_brightness' in settings:
            gesture.auto_brightness = bool(settings['auto_brightness'])
        
        if 'brightness_alpha' in settings:
            gesture.brightness_alpha = float(settings['brightness_alpha'])
        
        if 'brightness_beta' in settings:
            gesture.brightness_beta = float(settings['brightness_beta'])
        
        if 'adaptive_frame_skip' in settings:
            gesture.adaptive_frame_skip = int(settings['adaptive_frame_skip'])
        
        return {
            "success": True,
            "message": "Settings updated",
            "current_settings": {
                "cursor_smoothing": gesture.cursor_smoothing,
                "pinch_threshold": gesture.pinch_threshold,
                "grab_threshold": gesture.grab_threshold,
                "auto_brightness": gesture.auto_brightness
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

