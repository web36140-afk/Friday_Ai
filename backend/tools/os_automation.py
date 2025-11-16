"""
OS Automation Tool
Control Windows operations, launch apps, keyboard/mouse control
"""
import sys
import subprocess
from typing import Dict, Any
from loguru import logger

from core.tool_manager import BaseTool


class OSAutomationTool(BaseTool):
    """Windows OS automation tool"""
    
    name = "os_automation"
    description = "Automate Windows operations"
    
    def __init__(self):
        super().__init__()
        
        # Import Windows-specific modules
        if sys.platform == "win32":
            try:
                import pyautogui
                import win32gui
                import win32con
                import win32api
                
                self.pyautogui = pyautogui
                self.win32gui = win32gui
                self.win32con = win32con
                self.win32api = win32api
                
                # Set PyAutoGUI safety
                self.pyautogui.FAILSAFE = True
                self.pyautogui.PAUSE = 0.1
            except ImportError as e:
                logger.warning(f"Windows automation modules not available: {e}")
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute OS automation operation"""
        operations = {
            "launch_app": self.launch_application,
            "keyboard": self.keyboard_input,
            "mouse_move": self.mouse_move,
            "mouse_click": self.mouse_click,
            "screenshot": self.take_screenshot,
            "window_list": self.list_windows,
            "window_focus": self.focus_window,
            "system_command": self.system_command,
            "notify": self.show_notification
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
            logger.error(f"OS automation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }
    
    async def launch_application(self, application: str, args: str = "") -> Dict[str, Any]:
        """Launch an application"""
        try:
            if sys.platform == "win32":
                # Windows application launching
                cmd = f'start "" "{application}" {args}'
                subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen([application] + args.split())
            
            return {
                "success": True,
                "application": application,
                "message": f"Launched {application}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def keyboard_input(self, text: str = None, keys: str = None) -> Dict[str, Any]:
        """Simulate keyboard input"""
        if not hasattr(self, 'pyautogui'):
            return {"error": "PyAutoGUI not available"}
        
        try:
            if text:
                self.pyautogui.write(text, interval=0.05)
            
            if keys:
                # Parse hotkey combination (e.g., "ctrl+c", "alt+tab")
                key_list = keys.split('+')
                if len(key_list) > 1:
                    self.pyautogui.hotkey(*key_list)
                else:
                    self.pyautogui.press(keys)
            
            return {
                "success": True,
                "text": text,
                "keys": keys
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def mouse_move(self, x: int, y: int, duration: float = 0.5) -> Dict[str, Any]:
        """Move mouse to coordinates"""
        if not hasattr(self, 'pyautogui'):
            return {"error": "PyAutoGUI not available"}
        
        try:
            self.pyautogui.moveTo(x, y, duration=duration)
            
            return {
                "success": True,
                "position": {"x": x, "y": y}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def mouse_click(
        self,
        x: int = None,
        y: int = None,
        button: str = "left",
        clicks: int = 1
    ) -> Dict[str, Any]:
        """Click mouse"""
        if not hasattr(self, 'pyautogui'):
            return {"error": "PyAutoGUI not available"}
        
        try:
            if x is not None and y is not None:
                self.pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                self.pyautogui.click(clicks=clicks, button=button)
            
            return {
                "success": True,
                "button": button,
                "clicks": clicks
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def take_screenshot(self, path: str = None) -> Dict[str, Any]:
        """Take a screenshot"""
        if not hasattr(self, 'pyautogui'):
            return {"error": "PyAutoGUI not available"}
        
        try:
            if path:
                screenshot = self.pyautogui.screenshot(path)
            else:
                screenshot = self.pyautogui.screenshot()
            
            return {
                "success": True,
                "path": path or "memory",
                "size": screenshot.size if hasattr(screenshot, 'size') else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_windows(self) -> Dict[str, Any]:
        """List open windows"""
        if sys.platform != "win32":
            return {"error": "Windows-only operation"}
        
        try:
            windows = []
            
            def enum_callback(hwnd, windows):
                if self.win32gui.IsWindowVisible(hwnd):
                    title = self.win32gui.GetWindowText(hwnd)
                    if title:
                        windows.append({
                            "hwnd": hwnd,
                            "title": title
                        })
            
            self.win32gui.EnumWindows(enum_callback, windows)
            
            return {
                "success": True,
                "windows": windows,
                "total": len(windows)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def focus_window(self, title: str = None, hwnd: int = None) -> Dict[str, Any]:
        """Focus a window by title or handle"""
        if sys.platform != "win32":
            return {"error": "Windows-only operation"}
        
        try:
            if hwnd:
                window_handle = hwnd
            elif title:
                window_handle = self.win32gui.FindWindow(None, title)
                if not window_handle:
                    return {"error": f"Window not found: {title}"}
            else:
                return {"error": "Provide either title or hwnd"}
            
            # Bring window to front
            self.win32gui.SetForegroundWindow(window_handle)
            
            return {
                "success": True,
                "hwnd": window_handle
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def system_command(self, command: str) -> Dict[str, Any]:
        """Execute system command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def show_notification(
        self,
        title: str,
        message: str,
        duration: int = 5
    ) -> Dict[str, Any]:
        """Show Windows notification"""
        if sys.platform != "win32":
            return {"error": "Windows-only operation"}
        
        try:
            # Use PowerShell to show notification
            ps_command = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
            </toast>
"@
            
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("JARVIS").Show($toast)
            '''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=5
            )
            
            return {
                "success": True,
                "title": title,
                "message": message
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

