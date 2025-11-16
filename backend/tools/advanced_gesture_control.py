"""
ADVANCED GESTURE CONTROL - Full Desktop Automation
Professional-grade gesture recognition with OS-level control
Works in low light, blur, and bright conditions
"""

import sys
import time
import json
from typing import Dict, Any, List, Tuple, Optional
from loguru import logger
import pyautogui
import numpy as np

# Windows-specific imports
if sys.platform == "win32":
    import win32gui
    import win32con
    import win32api
    import win32process
    import ctypes
    from ctypes import wintypes

from core.tool_manager import BaseTool


class AdvancedGestureControl(BaseTool):
    """Advanced gesture control with full desktop automation"""
    
    name = "advanced_gesture_control"
    description = "Full desktop control via hand gestures - cursor, windows, apps, files"
    
    def __init__(self):
        super().__init__()
        
        # Cursor smoothing parameters
        self.cursor_smoothing = 0.3  # Lower = smoother (0.1-0.5)
        self.cursor_speed = 2.0       # Cursor movement multiplier
        self.last_cursor_pos = None
        
        # Gesture recognition parameters
        self.pinch_threshold = 0.05   # Distance for pinch detection
        self.swipe_threshold = 100    # Pixels for swipe detection
        self.gesture_cooldown = 0.3   # Seconds between gestures
        self.last_gesture_time = 0
        
        # Virtual cursor state
        self.virtual_cursor_active = False
        self.is_dragging = False
        self.drag_start_pos = None
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Disable PyAutoGUI failsafe for full control
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01  # Minimal delay for speed
        
        logger.info("🖐️ Advanced Gesture Control initialized")
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute gesture control operation"""
        
        operations = {
            # Cursor control
            "move_cursor": self.move_cursor,
            "click": self.perform_click,
            "double_click": self.perform_double_click,
            "right_click": self.perform_right_click,
            "drag_start": self.start_drag,
            "drag_move": self.continue_drag,
            "drag_end": self.end_drag,
            
            # Window management
            "maximize_window": self.maximize_active_window,
            "minimize_window": self.minimize_active_window,
            "close_window": self.close_active_window,
            "snap_left": self.snap_window_left,
            "snap_right": self.snap_window_right,
            "move_window": self.move_window,
            "resize_window": self.resize_window,
            
            # Desktop control
            "scroll": self.perform_scroll,
            "zoom": self.perform_zoom,
            "switch_desktop": self.switch_virtual_desktop,
            "show_desktop": self.show_desktop,
            
            # Application control
            "launch_app": self.launch_application,
            "switch_app": self.switch_application,
            "alt_tab": self.alt_tab,
            
            # Multi-monitor
            "move_to_monitor": self.move_window_to_monitor,
            "get_monitors": self.get_monitor_info,
            
            # Advanced gestures
            "rotate": self.handle_rotation,
            "pinch_zoom": self.handle_pinch_zoom,
            "three_finger_swipe": self.three_finger_swipe,
            
            # Calibration
            "calibrate": self.calibrate_tracking,
            "get_settings": self.get_current_settings,
            "update_settings": self.update_settings,
        }
        
        if operation not in operations:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
                "available": list(operations.keys())
            }
        
        try:
            result = await operations[operation](**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Gesture control error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    # ============================================
    # CURSOR CONTROL - Smooth & Precise
    # ============================================
    
    async def move_cursor(
        self,
        x: float,
        y: float,
        smooth: bool = True,
        relative: bool = False
    ) -> Dict[str, Any]:
        """
        Move cursor with advanced smoothing
        
        Args:
            x, y: Target position (0-1 normalized or absolute pixels)
            smooth: Apply exponential smoothing
            relative: Relative to current position
        """
        try:
            # Convert normalized coordinates to screen pixels if needed
            if 0 <= x <= 1 and 0 <= y <= 1:
                target_x = int(x * self.screen_width)
                target_y = int(y * self.screen_height)
            else:
                target_x = int(x)
                target_y = int(y)
            
            if relative:
                current_x, current_y = pyautogui.position()
                target_x += current_x
                target_y += current_y
            
            # Apply smoothing for natural movement
            if smooth and self.last_cursor_pos:
                last_x, last_y = self.last_cursor_pos
                # Exponential smoothing
                smooth_x = last_x + (target_x - last_x) * self.cursor_smoothing
                smooth_y = last_y + (target_y - last_y) * self.cursor_smoothing
                target_x, target_y = int(smooth_x), int(smooth_y)
            
            # Move cursor
            pyautogui.moveTo(target_x, target_y, duration=0)
            
            self.last_cursor_pos = (target_x, target_y)
            
            return {
                "position": {"x": target_x, "y": target_y},
                "normalized": {"x": target_x / self.screen_width, "y": target_y / self.screen_height}
            }
            
        except Exception as e:
            logger.error(f"Cursor move error: {e}")
            return {"error": str(e)}
    
    async def perform_click(self, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        """Perform mouse click"""
        pyautogui.click(button=button, clicks=clicks)
        return {"clicked": button, "count": clicks}
    
    async def perform_double_click(self) -> Dict[str, Any]:
        """Double click"""
        pyautogui.doubleClick()
        return {"action": "double_click"}
    
    async def perform_right_click(self) -> Dict[str, Any]:
        """Right click for context menu"""
        pyautogui.rightClick()
        return {"action": "right_click"}
    
    # ============================================
    # DRAG & DROP - Full Control
    # ============================================
    
    async def start_drag(self, x: Optional[float] = None, y: Optional[float] = None) -> Dict[str, Any]:
        """Start dragging operation"""
        if x is not None and y is not None:
            await self.move_cursor(x, y)
        
        pyautogui.mouseDown()
        self.is_dragging = True
        self.drag_start_pos = pyautogui.position()
        
        return {"dragging": True, "start_pos": self.drag_start_pos}
    
    async def continue_drag(self, x: float, y: float) -> Dict[str, Any]:
        """Continue dragging to new position"""
        if not self.is_dragging:
            return {"error": "Not currently dragging"}
        
        await self.move_cursor(x, y, smooth=True)
        return {"dragging": True, "current_pos": pyautogui.position()}
    
    async def end_drag(self) -> Dict[str, Any]:
        """End dragging operation"""
        if not self.is_dragging:
            return {"error": "Not currently dragging"}
        
        pyautogui.mouseUp()
        self.is_dragging = False
        end_pos = pyautogui.position()
        
        return {
            "dragging": False,
            "start_pos": self.drag_start_pos,
            "end_pos": end_pos
        }
    
    # ============================================
    # WINDOW MANAGEMENT - Full Control
    # ============================================
    
    async def maximize_active_window(self) -> Dict[str, Any]:
        """Maximize the active window"""
        if sys.platform == "win32":
            hwnd = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return {"window": self._get_window_title(hwnd), "action": "maximized"}
        else:
            pyautogui.hotkey('win', 'up')
            return {"action": "maximized"}
    
    async def minimize_active_window(self) -> Dict[str, Any]:
        """Minimize the active window"""
        if sys.platform == "win32":
            hwnd = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return {"window": self._get_window_title(hwnd), "action": "minimized"}
        else:
            pyautogui.hotkey('win', 'down')
            return {"action": "minimized"}
    
    async def close_active_window(self) -> Dict[str, Any]:
        """Close the active window"""
        pyautogui.hotkey('alt', 'f4')
        return {"action": "closed"}
    
    async def snap_window_left(self) -> Dict[str, Any]:
        """Snap window to left half of screen"""
        pyautogui.hotkey('win', 'left')
        return {"action": "snapped_left"}
    
    async def snap_window_right(self) -> Dict[str, Any]:
        """Snap window to right half of screen"""
        pyautogui.hotkey('win', 'right')
        return {"action": "snapped_right"}
    
    async def move_window(self, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
        """Move and resize window to specific position"""
        if sys.platform == "win32":
            hwnd = win32gui.GetForegroundWindow()
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            return {
                "window": self._get_window_title(hwnd),
                "position": {"x": x, "y": y, "width": width, "height": height}
            }
        return {"error": "Platform not supported"}
    
    async def resize_window(self, width: int, height: int) -> Dict[str, Any]:
        """Resize current window"""
        if sys.platform == "win32":
            hwnd = win32gui.GetForegroundWindow()
            rect = win32gui.GetWindowRect(hwnd)
            x, y = rect[0], rect[1]
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            return {"width": width, "height": height}
        return {"error": "Platform not supported"}
    
    # ============================================
    # DESKTOP CONTROL
    # ============================================
    
    async def perform_scroll(self, direction: str = "down", amount: int = 3) -> Dict[str, Any]:
        """Scroll up or down"""
        scroll_amount = amount if direction == "up" else -amount
        pyautogui.scroll(scroll_amount * 120)  # 120 units per notch
        return {"scrolled": direction, "amount": amount}
    
    async def perform_zoom(self, direction: str = "in") -> Dict[str, Any]:
        """Zoom in or out"""
        key = "+" if direction == "in" else "-"
        pyautogui.hotkey('ctrl', key)
        return {"zoomed": direction}
    
    async def switch_virtual_desktop(self, direction: str = "right") -> Dict[str, Any]:
        """Switch between virtual desktops"""
        arrow = "right" if direction == "right" else "left"
        pyautogui.hotkey('win', 'ctrl', arrow)
        return {"switched": direction}
    
    async def show_desktop(self) -> Dict[str, Any]:
        """Show desktop (minimize all windows)"""
        pyautogui.hotkey('win', 'd')
        return {"action": "show_desktop"}
    
    # ============================================
    # APPLICATION CONTROL
    # ============================================
    
    async def launch_application(self, app_name: str) -> Dict[str, Any]:
        """Launch application by name"""
        try:
            # Open run dialog
            pyautogui.hotkey('win', 'r')
            time.sleep(0.3)
            
            # Type app name
            pyautogui.write(app_name, interval=0.05)
            pyautogui.press('enter')
            
            return {"launched": app_name}
        except Exception as e:
            return {"error": str(e)}
    
    async def switch_application(self) -> Dict[str, Any]:
        """Switch between applications (Alt+Tab)"""
        pyautogui.hotkey('alt', 'tab')
        return {"action": "switched_app"}
    
    async def alt_tab(self, hold_time: float = 0.5) -> Dict[str, Any]:
        """Hold Alt+Tab for app switching"""
        pyautogui.keyDown('alt')
        time.sleep(0.1)
        pyautogui.press('tab')
        time.sleep(hold_time)
        pyautogui.keyUp('alt')
        return {"action": "alt_tab"}
    
    # ============================================
    # MULTI-MONITOR SUPPORT
    # ============================================
    
    async def get_monitor_info(self) -> Dict[str, Any]:
        """Get information about all monitors"""
        if sys.platform == "win32":
            monitors = []
            
            def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                monitors.append({
                    "left": lprcMonitor[0],
                    "top": lprcMonitor[1],
                    "right": lprcMonitor[2],
                    "bottom": lprcMonitor[3],
                    "width": lprcMonitor[2] - lprcMonitor[0],
                    "height": lprcMonitor[3] - lprcMonitor[1]
                })
                return True
            
            try:
                # Get all monitors
                ctypes.windll.user32.EnumDisplayMonitors(None, None, 
                    ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int, 
                    ctypes.POINTER(ctypes.c_int), ctypes.c_int)(callback), 0)
                
                return {"monitors": monitors, "count": len(monitors)}
            except:
                pass
        
        # Fallback to single monitor
        return {
            "monitors": [{
                "left": 0,
                "top": 0,
                "right": self.screen_width,
                "bottom": self.screen_height,
                "width": self.screen_width,
                "height": self.screen_height
            }],
            "count": 1
        }
    
    async def move_window_to_monitor(self, monitor_index: int = 1) -> Dict[str, Any]:
        """Move current window to specified monitor"""
        monitors_result = await self.get_monitor_info()
        monitors = monitors_result.get("monitors", [])
        
        if monitor_index >= len(monitors):
            return {"error": "Monitor index out of range"}
        
        target_monitor = monitors[monitor_index]
        
        # Move window to center of target monitor
        x = target_monitor["left"] + target_monitor["width"] // 4
        y = target_monitor["top"] + target_monitor["height"] // 4
        width = target_monitor["width"] // 2
        height = target_monitor["height"] // 2
        
        return await self.move_window(x, y, width, height)
    
    # ============================================
    # ADVANCED GESTURES
    # ============================================
    
    async def handle_rotation(self, angle: float) -> Dict[str, Any]:
        """Handle rotation gesture"""
        # Can be used for rotating images, pages, etc.
        if angle > 30:
            pyautogui.hotkey('ctrl', 'r')  # Rotate right
            return {"rotated": "right", "angle": angle}
        elif angle < -30:
            pyautogui.hotkey('ctrl', 'l')  # Rotate left
            return {"rotated": "left", "angle": angle}
        return {"action": "no_rotation"}
    
    async def handle_pinch_zoom(self, scale: float) -> Dict[str, Any]:
        """Handle pinch to zoom gesture"""
        if scale > 1.2:
            await self.perform_zoom("in")
            return {"zoomed": "in", "scale": scale}
        elif scale < 0.8:
            await self.perform_zoom("out")
            return {"zoomed": "out", "scale": scale}
        return {"action": "no_zoom"}
    
    async def three_finger_swipe(self, direction: str) -> Dict[str, Any]:
        """Three finger swipe for advanced navigation"""
        if direction == "left":
            pyautogui.hotkey('alt', 'left')  # Browser back
        elif direction == "right":
            pyautogui.hotkey('alt', 'right')  # Browser forward
        elif direction == "up":
            pyautogui.hotkey('win', 'tab')  # Task view
        elif direction == "down":
            await self.show_desktop()
        
        return {"swipe": direction}
    
    # ============================================
    # CALIBRATION & SETTINGS
    # ============================================
    
    async def calibrate_tracking(self, 
                                 smoothing: Optional[float] = None,
                                 speed: Optional[float] = None) -> Dict[str, Any]:
        """Calibrate tracking parameters"""
        if smoothing is not None:
            self.cursor_smoothing = max(0.1, min(0.9, smoothing))
        
        if speed is not None:
            self.cursor_speed = max(0.5, min(5.0, speed))
        
        return {
            "smoothing": self.cursor_smoothing,
            "speed": self.cursor_speed,
            "message": "Calibration updated"
        }
    
    async def get_current_settings(self) -> Dict[str, Any]:
        """Get current gesture control settings"""
        return {
            "cursor_smoothing": self.cursor_smoothing,
            "cursor_speed": self.cursor_speed,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "pinch_threshold": self.pinch_threshold,
            "swipe_threshold": self.swipe_threshold,
            "gesture_cooldown": self.gesture_cooldown
        }
    
    async def update_settings(self, **settings) -> Dict[str, Any]:
        """Update gesture control settings"""
        updated = []
        
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
                updated.append(key)
        
        return {
            "updated": updated,
            "current_settings": await self.get_current_settings()
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _get_window_title(self, hwnd) -> str:
        """Get window title from handle"""
        try:
            return win32gui.GetWindowText(hwnd)
        except:
            return "Unknown Window"
    
    def _check_gesture_cooldown(self) -> bool:
        """Check if enough time has passed since last gesture"""
        current_time = time.time()
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return False
        self.last_gesture_time = current_time
        return True


# Tool instance
tool_instance = AdvancedGestureControl()

