"""
Media Control Tool
Control music playback, media keys, Spotify, etc.
"""
import sys
import subprocess
from typing import Dict, Any
from loguru import logger

from core.tool_manager import BaseTool


class MediaControlTool(BaseTool):
    """Control media playback and music apps"""
    
    name = "media_control"
    description = "Control music playback (play, pause, next, previous)"
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute media control operation"""
        operations = {
            "play_pause": self.play_pause,
            "next_track": self.next_track,
            "previous_track": self.previous_track,
            "stop": self.stop_playback,
            "volume_up": self.volume_up,
            "volume_down": self.volume_down,
            "mute": self.mute_toggle
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
            logger.error(f"Media control error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }
    
    async def play_pause(self) -> Dict[str, Any]:
        """Toggle play/pause"""
        try:
            # Send media key via PowerShell
            ps_command = '''
Add-Type -AssemblyName System.Windows.Forms
$wsh = New-Object -ComObject WScript.Shell
$wsh.SendKeys([char]179)
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=2
            )
            
            return {
                "success": True,
                "operation": "play_pause",
                "message": "Toggled play/pause"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def next_track(self) -> Dict[str, Any]:
        """Next track"""
        try:
            ps_command = '''
Add-Type -AssemblyName System.Windows.Forms
$wsh = New-Object -ComObject WScript.Shell
$wsh.SendKeys([char]176)
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=2
            )
            
            return {
                "success": True,
                "operation": "next_track",
                "message": "Next track"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def previous_track(self) -> Dict[str, Any]:
        """Previous track"""
        try:
            ps_command = '''
Add-Type -AssemblyName System.Windows.Forms
$wsh = New-Object -ComObject WScript.Shell
$wsh.SendKeys([char]177)
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=2
            )
            
            return {
                "success": True,
                "operation": "previous_track",
                "message": "Previous track"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def stop_playback(self) -> Dict[str, Any]:
        """Stop playback"""
        try:
            ps_command = '''
Add-Type -AssemblyName System.Windows.Forms
$wsh = New-Object -ComObject WScript.Shell
$wsh.SendKeys([char]178)
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=2
            )
            
            return {
                "success": True,
                "operation": "stop",
                "message": "Stopped playback"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def volume_up(self) -> Dict[str, Any]:
        """Volume up via media key"""
        try:
            ps_command = '''
$obj = New-Object -ComObject WScript.Shell
1..2 | ForEach-Object { $obj.SendKeys([char]175) }
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=2
            )
            
            return {
                "success": True,
                "operation": "volume_up",
                "message": "Volume increased"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def volume_down(self) -> Dict[str, Any]:
        """Volume down via media key"""
        try:
            ps_command = '''
$obj = New-Object -ComObject WScript.Shell
1..2 | ForEach-Object { $obj.SendKeys([char]174) }
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=2
            )
            
            return {
                "success": True,
                "operation": "volume_down",
                "message": "Volume decreased"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def mute_toggle(self) -> Dict[str, Any]:
        """Toggle mute"""
        try:
            ps_command = '(New-Object -ComObject WScript.Shell).SendKeys([char]173)'
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=2
            )
            
            return {
                "success": True,
                "operation": "mute",
                "message": "Mute toggled"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_args(self, operation: str = None, **kwargs) -> bool:
        """Validate arguments"""
        return bool(operation)

