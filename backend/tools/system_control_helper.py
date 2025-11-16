"""
System Control Helper
Handles Windows system operations with UAC permission management
"""

import sys
import os
import ctypes
import subprocess
from typing import Dict, Any, Optional
from loguru import logger


class SystemControlHelper:
    """Helper for system control operations with UAC handling"""
    
    def __init__(self):
        self.is_admin = self._check_admin_privileges()
        logger.info(f"🔐 System Control Helper initialized (Admin: {self.is_admin})")
    
    def _check_admin_privileges(self) -> bool:
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def request_admin_privileges(self) -> bool:
        """Request UAC elevation (restart with admin rights)"""
        try:
            if self.is_admin:
                return True
            
            logger.info("⚠️ Admin privileges required, requesting UAC elevation...")
            
            # Get current script path
            script = sys.argv[0]
            params = ' '.join(sys.argv[1:])
            
            # Request elevation
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Run as administrator
                sys.executable,
                f'"{script}" {params}',
                None,
                1  # SW_SHOWNORMAL
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to request admin privileges: {e}")
            return False
    
    def execute_with_privileges(self, command: str, require_admin: bool = False) -> Dict[str, Any]:
        """
        Execute command with appropriate privileges
        
        Args:
            command: Command to execute
            require_admin: Whether admin rights are required
        """
        try:
            if require_admin and not self.is_admin:
                logger.warning("⚠️ Admin rights required but not available")
                return {
                    "success": False,
                    "error": "Administrator privileges required",
                    "solution": "Please run FRIDAY as administrator for this operation"
                }
            
            # Execute command
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
                "error": result.stderr if result.returncode != 0 else None
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
    
    # ============================================
    # SAFE OPERATIONS (No UAC needed)
    # ============================================
    
    def safe_shutdown(self, delay: int = 30) -> Dict[str, Any]:
        """Shutdown computer (no admin needed with delay)"""
        return self.execute_with_privileges(
            f'shutdown /s /t {delay}',
            require_admin=False
        )
    
    def safe_restart(self, delay: int = 30) -> Dict[str, Any]:
        """Restart computer (no admin needed with delay)"""
        return self.execute_with_privileges(
            f'shutdown /r /t {delay}',
            require_admin=False
        )
    
    def cancel_shutdown(self) -> Dict[str, Any]:
        """Cancel pending shutdown/restart"""
        return self.execute_with_privileges(
            'shutdown /a',
            require_admin=False
        )
    
    def lock_computer(self) -> Dict[str, Any]:
        """Lock workstation (no admin needed)"""
        try:
            ctypes.windll.user32.LockWorkStation()
            return {"success": True, "action": "locked"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sleep_computer(self) -> Dict[str, Any]:
        """Put computer to sleep (no admin needed)"""
        return self.execute_with_privileges(
            'rundll32.exe powrprof.dll,SetSuspendState 0,1,0',
            require_admin=False
        )
    
    def hibernate_computer(self) -> Dict[str, Any]:
        """Hibernate computer (may need admin)"""
        return self.execute_with_privileges(
            'shutdown /h',
            require_admin=False  # Usually doesn't need admin
        )
    
    # ============================================
    # POWER MANAGEMENT
    # ============================================
    
    def get_battery_status(self) -> Dict[str, Any]:
        """Get battery status (no admin needed)"""
        try:
            import psutil
            battery = psutil.sensors_battery()
            
            if battery is None:
                return {
                    "success": True,
                    "has_battery": False,
                    "message": "No battery detected (desktop PC)"
                }
            
            return {
                "success": True,
                "has_battery": True,
                "percent": battery.percent,
                "charging": battery.power_plugged,
                "time_left": battery.secsleft if not battery.power_plugged else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_power_plan(self, plan: str = "balanced") -> Dict[str, Any]:
        """Set Windows power plan (may need admin)"""
        
        plans = {
            "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
            "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
            "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a"
        }
        
        plan_guid = plans.get(plan.lower())
        if not plan_guid:
            return {"success": False, "error": "Invalid power plan"}
        
        return self.execute_with_privileges(
            f'powercfg /setactive {plan_guid}',
            require_admin=True  # Needs admin
        )
    
    # ============================================
    # PROCESS MANAGEMENT
    # ============================================
    
    def kill_process(self, process_name: str, force: bool = False) -> Dict[str, Any]:
        """Kill process by name (may need admin for system processes)"""
        
        flag = "/F" if force else ""
        return self.execute_with_privileges(
            f'taskkill {flag} /IM {process_name}',
            require_admin=force  # Force kill needs admin
        )
    
    def get_running_processes(self) -> Dict[str, Any]:
        """Get list of running processes (no admin needed)"""
        try:
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu": proc.info['cpu_percent'],
                        "memory": proc.info['memory_percent']
                    })
                except:
                    continue
            
            return {
                "success": True,
                "processes": processes[:50],  # Limit to 50
                "total_count": len(processes)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================
    # NETWORK OPERATIONS
    # ============================================
    
    def disable_wifi(self) -> Dict[str, Any]:
        """Disable WiFi (needs admin)"""
        return self.execute_with_privileges(
            'netsh interface set interface "Wi-Fi" disabled',
            require_admin=True
        )
    
    def enable_wifi(self) -> Dict[str, Any]:
        """Enable WiFi (needs admin)"""
        return self.execute_with_privileges(
            'netsh interface set interface "Wi-Fi" enabled',
            require_admin=True
        )
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information (no admin needed)"""
        try:
            import psutil
            
            interfaces = {}
            for name, addrs in psutil.net_if_addrs().items():
                interfaces[name] = []
                for addr in addrs:
                    interfaces[name].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    })
            
            stats = psutil.net_if_stats()
            
            return {
                "success": True,
                "interfaces": interfaces,
                "stats": {
                    name: {
                        "isup": stat.isup,
                        "speed": stat.speed,
                        "mtu": stat.mtu
                    }
                    for name, stat in stats.items()
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================
    # VOLUME & MEDIA CONTROL
    # ============================================
    
    def set_volume(self, level: int) -> Dict[str, Any]:
        """Set system volume (0-100) (no admin needed)"""
        try:
            from tools.windows_control import tool_instance as windows_tool
            result = windows_tool.set_volume(level)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def mute_audio(self) -> Dict[str, Any]:
        """Mute system audio (no admin needed)"""
        try:
            from tools.windows_control import tool_instance as windows_tool
            result = windows_tool.mute_volume()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================
    # DISPLAY CONTROL
    # ============================================
    
    def turn_off_display(self) -> Dict[str, Any]:
        """Turn off display (no admin needed)"""
        try:
            import win32gui
            import win32con
            
            win32gui.SendMessage(
                win32con.HWND_BROADCAST,
                win32con.WM_SYSCOMMAND,
                win32con.SC_MONITORPOWER,
                2  # 2 = off, 1 = low power, -1 = on
            )
            
            return {"success": True, "action": "display_off"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def turn_on_display(self) -> Dict[str, Any]:
        """Turn on display (no admin needed)"""
        try:
            import win32gui
            import win32con
            
            win32gui.SendMessage(
                win32con.HWND_BROADCAST,
                win32con.WM_SYSCOMMAND,
                win32con.SC_MONITORPOWER,
                -1  # -1 = on
            )
            
            return {"success": True, "action": "display_on"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================
    # CLIPBOARD OPERATIONS
    # ============================================
    
    def get_clipboard(self) -> Dict[str, Any]:
        """Get clipboard content (no admin needed)"""
        try:
            import win32clipboard
            
            win32clipboard.OpenClipboard()
            try:
                text = win32clipboard.GetClipboardData()
                return {"success": True, "content": text}
            finally:
                win32clipboard.CloseClipboard()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_clipboard(self, text: str) -> Dict[str, Any]:
        """Set clipboard content (no admin needed)"""
        try:
            import win32clipboard
            
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                return {"success": True}
            finally:
                win32clipboard.CloseClipboard()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================
    # NOTIFICATION
    # ============================================
    
    def show_notification(self, title: str, message: str, duration: int = 5) -> Dict[str, Any]:
        """Show Windows notification (no admin needed)"""
        try:
            from plyer import notification
            
            notification.notify(
                title=title,
                message=message,
                app_name="FRIDAY AI Assistant",
                timeout=duration
            )
            
            return {"success": True}
            
        except Exception as e:
            # Fallback to PowerShell notification
            try:
                ps_script = f"""
                Add-Type -AssemblyName System.Windows.Forms
                $notify = New-Object System.Windows.Forms.NotifyIcon
                $notify.Icon = [System.Drawing.SystemIcons]::Information
                $notify.Visible = $true
                $notify.ShowBalloonTip(5000, '{title}', '{message}', [System.Windows.Forms.ToolTipIcon]::Info)
                """
                
                subprocess.run(['powershell', '-Command', ps_script], check=True)
                return {"success": True}
            except:
                return {"success": False, "error": str(e)}


# Global instance
system_helper = SystemControlHelper()

# Log admin status on load
if system_helper.is_admin:
    logger.info("✅ Running with Administrator privileges")
else:
    logger.warning("⚠️ Running without Administrator privileges (some features limited)")
    logger.info("💡 To enable all features, run FRIDAY as Administrator")

