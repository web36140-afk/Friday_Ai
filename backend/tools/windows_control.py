"""
Windows System Control Tool
Control volume, brightness, power, WiFi, Bluetooth, etc.
"""
import sys
import subprocess
from typing import Dict, Any
from loguru import logger

from core.tool_manager import BaseTool


class WindowsControlTool(BaseTool):
    """Windows system control tool for volume, brightness, power, etc."""
    
    name = "windows_control"
    description = "Control Windows system settings (volume, brightness, power, network)"
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute Windows control operation"""
        operations = {
            "volume_set": self.set_volume,
            "volume_up": self.volume_up,
            "volume_down": self.volume_down,
            "volume_mute": self.mute_toggle,
            "brightness_set": self.set_brightness,
            "shutdown": self.shutdown_pc,
            "restart": self.restart_pc,
            "sleep": self.sleep_pc,
            "lock": self.lock_pc,
            "wifi_toggle": self.toggle_wifi,
            "bluetooth_toggle": self.toggle_bluetooth,
            "open_app": self.open_application,
            "close_app": self.close_application
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
            logger.error(f"Windows control error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }
    
    async def set_volume(self, level: int) -> Dict[str, Any]:
        """Set system volume (0-100)"""
        if not 0 <= level <= 100:
            return {"error": "Volume must be between 0 and 100"}
        
        try:
            # Use nircmd if available, otherwise PowerShell
            ps_command = f'(New-Object -ComObject WScript.Shell).SendKeys([char]173)' if level == 0 else f'''
$obj = New-Object -ComObject WScript.Shell
1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
1..{level//2} | ForEach-Object {{ $obj.SendKeys([char]175) }}
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=5
            )
            
            return {
                "success": True,
                "operation": "volume_set",
                "level": level,
                "message": f"Volume set to {level}%"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def volume_up(self, step: int = 10) -> Dict[str, Any]:
        """Increase volume"""
        try:
            ps_command = f'''
$obj = New-Object -ComObject WScript.Shell
1..{step//2} | ForEach-Object {{ $obj.SendKeys([char]175) }}
'''
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=5
            )
            
            return {
                "success": True,
                "operation": "volume_up",
                "message": f"Volume increased by {step}%"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def volume_down(self, step: int = 10) -> Dict[str, Any]:
        """Decrease volume"""
        try:
            ps_command = f'''
$obj = New-Object -ComObject WScript.Shell
1..{step//2} | ForEach-Object {{ $obj.SendKeys([char]174) }}
'''
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=5
            )
            
            return {
                "success": True,
                "operation": "volume_down",
                "message": f"Volume decreased by {step}%"
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
                timeout=5
            )
            
            return {
                "success": True,
                "operation": "mute_toggle",
                "message": "Volume muted/unmuted"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def set_brightness(self, level: int) -> Dict[str, Any]:
        """Set screen brightness (0-100)"""
        if not 0 <= level <= 100:
            return {"error": "Brightness must be between 0 and 100"}
        
        try:
            ps_command = f'''
$brightness = {level}
(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, $brightness)
'''
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=5
            )
            
            return {
                "success": True,
                "operation": "brightness_set",
                "level": level,
                "message": f"Brightness set to {level}%"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def shutdown_pc(self, delay: int = 30) -> Dict[str, Any]:
        """Shutdown PC with optional delay (seconds)"""
        try:
            subprocess.run(
                ["shutdown", "/s", "/t", str(delay)],
                capture_output=True
            )
            
            return {
                "success": True,
                "operation": "shutdown",
                "delay": delay,
                "message": f"PC will shutdown in {delay} seconds"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def restart_pc(self, delay: int = 30) -> Dict[str, Any]:
        """Restart PC with optional delay (seconds)"""
        try:
            subprocess.run(
                ["shutdown", "/r", "/t", str(delay)],
                capture_output=True
            )
            
            return {
                "success": True,
                "operation": "restart",
                "delay": delay,
                "message": f"PC will restart in {delay} seconds"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sleep_pc(self) -> Dict[str, Any]:
        """Put PC to sleep"""
        try:
            ps_command = 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState("Suspend", $false, $false)'
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=5
            )
            
            return {
                "success": True,
                "operation": "sleep",
                "message": "PC going to sleep"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def lock_pc(self) -> Dict[str, Any]:
        """Lock PC"""
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            
            return {
                "success": True,
                "operation": "lock",
                "message": "PC locked"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def toggle_wifi(self) -> Dict[str, Any]:
        """Toggle WiFi on/off"""
        try:
            ps_command = '''
$adapter = Get-NetAdapter | Where-Object {$_.Name -like "*Wi-Fi*" -or $_.Name -like "*Wireless*"}
if ($adapter.Status -eq "Up") {
    Disable-NetAdapter -Name $adapter.Name -Confirm:$false
    Write-Output "disabled"
} else {
    Enable-NetAdapter -Name $adapter.Name -Confirm:$false
    Write-Output "enabled"
}
'''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            status = "enabled" if "enabled" in result.stdout.lower() else "disabled"
            
            return {
                "success": True,
                "operation": "wifi_toggle",
                "status": status,
                "message": f"WiFi {status}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def toggle_bluetooth(self) -> Dict[str, Any]:
        """Toggle Bluetooth on/off"""
        try:
            ps_command = '''
$bluetooth = Get-PnpDevice | Where-Object {$_.Class -eq "Bluetooth" -and $_.FriendlyName -like "*Bluetooth*"}
if ($bluetooth.Status -eq "OK") {
    Disable-PnpDevice -InstanceId $bluetooth.InstanceId -Confirm:$false
    Write-Output "disabled"
} else {
    Enable-PnpDevice -InstanceId $bluetooth.InstanceId -Confirm:$false
    Write-Output "enabled"
}
'''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            status = "enabled" if "enabled" in result.stdout.lower() else "disabled"
            
            return {
                "success": True,
                "operation": "bluetooth_toggle",
                "status": status,
                "message": f"Bluetooth {status}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open application by name"""
        # Common Windows apps mapping
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "firefox": "firefox.exe",
            "spotify": "spotify.exe",
            "discord": "discord.exe",
            "vscode": "code.exe",
            "vs code": "code.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            "cmd": "cmd.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe"
        }
        
        app_name_lower = app_name.lower()
        executable = app_map.get(app_name_lower, app_name)
        
        try:
            subprocess.Popen(executable, shell=True)
            
            return {
                "success": True,
                "operation": "open_app",
                "app": app_name,
                "message": f"Opened {app_name}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close_application(self, app_name: str) -> Dict[str, Any]:
        """Close application by name"""
        try:
            # Use taskkill to close the process
            ps_command = f'Get-Process -Name "*{app_name}*" -ErrorAction SilentlyContinue | Stop-Process -Force'
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "success": True,
                "operation": "close_app",
                "app": app_name,
                "message": f"Closed {app_name}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_args(self, operation: str = None, **kwargs) -> bool:
        """Validate arguments"""
        return bool(operation)

