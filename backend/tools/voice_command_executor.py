"""
Advanced Voice Command Executor
Handles natural language commands for system control, file access, and web browsing
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
import re

from core.tool_manager import BaseTool
from tools.voice_command_helper import voice_helper
from tools.system_control_helper import system_helper
from tools.youtube_control import YouTubeControlTool


class VoiceCommandExecutor(BaseTool):
    """Execute voice commands with natural language understanding"""
    
    name = "voice_command_executor"
    description = "Execute system commands, open files/apps, control browsers via voice"
    
    def __init__(self):
        super().__init__()
        
        # Browser paths (auto-detect)
        self.browsers = self._detect_browsers()
        
        # YouTube control
        self.youtube = YouTubeControlTool()
        
        # Common app shortcuts
        self.app_shortcuts = {
            # Browsers
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            "opera": "opera.exe",
            
            # Office
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "notepad": "notepad.exe",
            "notepad++": r"C:\Program Files\Notepad++\notepad++.exe",
            
            # Development
            "vscode": "code.cmd",
            "visual studio code": "code.cmd",
            "pycharm": r"C:\Program Files\JetBrains\PyCharm\bin\pycharm64.exe",
            "sublime": r"C:\Program Files\Sublime Text\sublime_text.exe",
            
            # Media
            "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            "spotify": r"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe",
            "itunes": r"C:\Program Files\iTunes\iTunes.exe",
            
            # Communication
            "discord": r"C:\Users\{username}\AppData\Local\Discord\app-1.0.9015\Discord.exe",
            "slack": r"C:\Users\{username}\AppData\Local\slack\slack.exe",
            "teams": r"C:\Users\{username}\AppData\Local\Microsoft\Teams\current\Teams.exe",
            "zoom": r"C:\Users\{username}\AppData\Roaming\Zoom\bin\Zoom.exe",
            
            # System
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            "file explorer": "explorer.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
        }
        
        # Popular websites
        self.websites = {
            # Social Media
            "facebook": "https://www.facebook.com",
            "twitter": "https://www.twitter.com",
            "x": "https://www.x.com",
            "instagram": "https://www.instagram.com",
            "linkedin": "https://www.linkedin.com",
            "reddit": "https://www.reddit.com",
            "tiktok": "https://www.tiktok.com",
            "snapchat": "https://www.snapchat.com",
            
            # Professional
            "github": "https://www.github.com",
            "stackoverflow": "https://stackoverflow.com",
            "medium": "https://www.medium.com",
            
            # Entertainment
            "youtube": "https://www.youtube.com",
            "netflix": "https://www.netflix.com",
            "spotify web": "https://open.spotify.com",
            "twitch": "https://www.twitch.tv",
            
            # Email
            "gmail": "https://mail.google.com",
            "outlook web": "https://outlook.live.com",
            "yahoo mail": "https://mail.yahoo.com",
            
            # Work
            "google drive": "https://drive.google.com",
            "dropbox": "https://www.dropbox.com",
            "notion": "https://www.notion.so",
            "trello": "https://www.trello.com",
            "asana": "https://app.asana.com",
            
            # Search
            "google": "https://www.google.com",
            "bing": "https://www.bing.com",
            "duckduckgo": "https://www.duckduckgo.com",
        }
        
        # Command patterns for NLP
        self.command_patterns = {
            "open_app": [
                r"open (.+)",
                r"launch (.+)",
                r"start (.+)",
                r"run (.+)",
            ],
            "open_website": [
                r"go to (.+)",
                r"open website (.+)",
                r"visit (.+)",
                r"browse (.+)",
            ],
            "open_file": [
                r"open file (.+)",
                r"show me (.+)",
                r"access (.+)",
            ],
            "system_control": [
                r"(shutdown|restart|sleep|lock) (computer|pc|system)",
                r"(maximize|minimize|close) (window|this)",
                r"show desktop",
                r"switch (window|app)",
            ],
        }
        
        # Common desktop paths
        username = os.getlogin()
        self.common_paths = {
            "desktop": os.path.join(os.environ["USERPROFILE"], "Desktop"),
            "documents": os.path.join(os.environ["USERPROFILE"], "Documents"),
            "downloads": os.path.join(os.environ["USERPROFILE"], "Downloads"),
            "pictures": os.path.join(os.environ["USERPROFILE"], "Pictures"),
            "videos": os.path.join(os.environ["USERPROFILE"], "Videos"),
            "music": os.path.join(os.environ["USERPROFILE"], "Music"),
        }
        
        logger.info("🎙️ Voice Command Executor initialized")
    
    def _detect_browsers(self) -> Dict[str, str]:
        """Auto-detect installed browsers"""
        browsers = {}
        
        browser_paths = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            "opera": r"C:\Users\{username}\AppData\Local\Programs\Opera\opera.exe",
        }
        
        username = os.getlogin()
        for name, path in browser_paths.items():
            path = path.replace("{username}", username)
            if os.path.exists(path):
                browsers[name] = path
                logger.info(f"✅ Found browser: {name}")
        
        return browsers
    
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute voice command with natural language understanding"""
        
        # Clean command using helper
        command = voice_helper.clean_command(command)
        logger.info(f"🎙️ Processing voice command: {command}")
        
        # Detect intent
        intent_data = voice_helper.detect_intent(command)
        logger.info(f"🎯 Detected intent: {intent_data['intent']} (confidence: {intent_data['confidence']:.2f})")
        
        # Validate safety
        safety_check = voice_helper.validate_command_safety(command)
        if not safety_check["safe"]:
            return {
                "success": False,
                "error": "Unsafe command detected",
                "reason": safety_check["reason"],
                "requires_confirmation": safety_check["requires_confirmation"]
            }
        
        try:
            # Check for chained commands (e.g., "open brave and then linkedin")
            if " and then " in command or " then " in command:
                return await self._execute_chained_commands(command)
            
            # Parse and execute single command
            result = await self._parse_and_execute(command)
            
            return {"success": True, "result": result, "command": command}
            
        except Exception as e:
            logger.error(f"Command execution error: {e}", exc_info=True)
            return {"success": False, "error": str(e), "command": command}
    
    async def _execute_chained_commands(self, command: str) -> Dict[str, Any]:
        """Execute multiple commands in sequence"""
        
        # Use helper to extract chained commands
        parts = voice_helper.extract_chain_commands(command)
        
        results = []
        for i, part in enumerate(parts):
            logger.info(f"📋 Step {i+1}/{len(parts)}: {part}")
            
            result = await self._parse_and_execute(part.strip())
            results.append(result)
            
            # Small delay between commands
            if i < len(parts) - 1:
                time.sleep(1)
        
        return {
            "type": "chained_commands",
            "steps": len(parts),
            "results": results
        }
    
    async def _parse_and_execute(self, command: str) -> Dict[str, Any]:
        """Parse command and execute appropriate action"""
        
        # Special-case: "open youtube" should open default browser to youtube.com
        if "youtube" in command:
            # Pattern: "play <query> on youtube" or "search <query> on youtube"
            yt_play_pattern = r"(?:play|search)\s+(.+?)\s+(?:on|in)\s+youtube"
            m = re.search(yt_play_pattern, command, re.IGNORECASE)
            if m:
                query = m.group(1).strip()
                # Delegate to YouTube control (autoplay best effort)
                return await self.youtube.search_and_play(query=query, autoplay=True)
            # Otherwise, just open YouTube home
            return await self._open_website("youtube")
        
        # 1. Check for browser + website combo
        browser_website = self._parse_browser_website(command)
        if browser_website:
            return await self._open_browser_with_website(**browser_website)
        
        # 2. Check for website opening
        website = self._extract_website(command)
        if website:
            return await self._open_website(website)
        
        # 3. Check for app opening
        app = self._extract_app(command)
        if app:
            return await self._open_app(app)
        
        # 4. Check for file/folder access
        file_path = self._extract_file_path(command)
        if file_path:
            return await self._open_file(file_path)
        
        # 5. Check for system commands
        system_cmd = self._extract_system_command(command)
        if system_cmd:
            return await self._execute_system_command(system_cmd)
        
        # 6. Fallback: Try as direct command
        return await self._execute_direct_command(command)
    
    def _parse_browser_website(self, command: str) -> Optional[Dict[str, str]]:
        """Parse 'open [browser] and [website]' commands"""
        
        # Pattern: "open brave and linkedin"
        pattern = r"open\s+(\w+)(?:\s+and\s+|\s+then\s+)(\w+)"
        match = re.search(pattern, command)
        
        if match:
            browser_name = match.group(1)
            site_name = match.group(2)
            
            # Check if both exist
            if browser_name in self.browsers and site_name in self.websites:
                return {
                    "browser": browser_name,
                    "website": site_name,
                    "url": self.websites[site_name]
                }
        
        return None
    
    async def _open_browser_with_website(self, browser: str, website: str, url: str) -> Dict[str, Any]:
        """Open specific browser with specific website"""
        
        browser_path = self.browsers.get(browser)
        
        if not browser_path:
            # Fallback to default browser
            webbrowser.open(url)
            return {
                "action": "open_website",
                "browser": "default",
                "website": website,
                "url": url
            }
        
        # Open browser with URL
        subprocess.Popen([browser_path, url])
        
        logger.info(f"✅ Opened {website} in {browser}")
        
        return {
            "action": "open_browser_website",
            "browser": browser,
            "website": website,
            "url": url
        }
    
    def _extract_website(self, command: str) -> Optional[str]:
        """Extract website name from command"""
        
        for site_name, url in self.websites.items():
            if site_name in command:
                return site_name
        
        # Check for direct URL
        url_pattern = r"https?://[\w\.-]+\.\w+"
        match = re.search(url_pattern, command)
        if match:
            return match.group(0)
        
        return None
    
    async def _open_website(self, site_identifier: str) -> Dict[str, Any]:
        """Open website in default browser"""
        
        # Check if it's a known site
        if site_identifier in self.websites:
            url = self.websites[site_identifier]
        else:
            # Treat as direct URL
            url = site_identifier if site_identifier.startswith("http") else f"https://{site_identifier}"
        
        webbrowser.open(url)
        
        logger.info(f"✅ Opened website: {url}")
        
        return {
            "action": "open_website",
            "site": site_identifier,
            "url": url
        }
    
    def _extract_app(self, command: str) -> Optional[str]:
        """Extract application name from command"""
        
        # Normalize command
        command = voice_helper.normalize_app_name(command)
        
        # Try direct match first
        for app_name in self.app_shortcuts.keys():
            if app_name in command:
                return app_name
        
        # Try fuzzy matching for typos/variations
        fuzzy_match = voice_helper.fuzzy_match_app(
            command,
            list(self.app_shortcuts.keys()),
            threshold=0.7
        )
        if fuzzy_match:
            return fuzzy_match
        
        # Try pattern matching
        for pattern in self.command_patterns["open_app"]:
            match = re.search(pattern, command)
            if match:
                app_name = match.group(1).strip()
                if app_name in self.app_shortcuts:
                    return app_name
        
        return None
    
    async def _open_app(self, app_name: str) -> Dict[str, Any]:
        """Open application"""
        
        app_path = self.app_shortcuts.get(app_name)
        
        if not app_path:
            return {"error": f"App '{app_name}' not found"}
        
        # Replace username placeholder
        username = os.getlogin()
        app_path = app_path.replace("{username}", username)
        
        try:
            if app_path.startswith("ms-"):
                # Windows URI scheme
                os.startfile(app_path)
            elif os.path.exists(app_path):
                subprocess.Popen(app_path)
            else:
                # Try as command
                subprocess.Popen(app_path, shell=True)
            
            logger.info(f"✅ Opened app: {app_name}")
            
            return {
                "action": "open_app",
                "app": app_name,
                "path": app_path
            }
            
        except Exception as e:
            logger.error(f"Failed to open app {app_name}: {e}")
            return {"error": str(e)}
    
    def _extract_file_path(self, command: str) -> Optional[str]:
        """Extract file or folder path from command"""
        
        # Check for common locations
        for location_name, location_path in self.common_paths.items():
            if location_name in command:
                return location_path
        
        # Check for specific file patterns
        file_pattern = r"(?:file|folder|directory)\s+(.+)"
        match = re.search(file_pattern, command)
        if match:
            filename = match.group(1).strip()
            
            # Search in common locations
            for path in self.common_paths.values():
                full_path = os.path.join(path, filename)
                if os.path.exists(full_path):
                    return full_path
        
        return None
    
    async def _open_file(self, file_path: str) -> Dict[str, Any]:
        """Open file or folder"""
        
        if not os.path.exists(file_path):
            return {"error": f"Path not found: {file_path}"}
        
        os.startfile(file_path)
        
        logger.info(f"✅ Opened: {file_path}")
        
        return {
            "action": "open_file",
            "path": file_path,
            "type": "folder" if os.path.isdir(file_path) else "file"
        }
    
    def _extract_system_command(self, command: str) -> Optional[Dict[str, str]]:
        """Extract system control command"""
        
        system_commands = {
            "shutdown": {"action": "shutdown", "delay": 30},
            "restart": {"action": "restart", "delay": 30},
            "sleep": {"action": "sleep"},
            "lock": {"action": "lock"},
            "show desktop": {"action": "show_desktop"},
            "minimize": {"action": "minimize_window"},
            "maximize": {"action": "maximize_window"},
            "close window": {"action": "close_window"},
            # Media & volume controls
            "pause": {"action": "media_play_pause"},
            "play": {"action": "media_play_pause"},
            "next": {"action": "media_next"},
            "previous": {"action": "media_prev"},
            "volume up": {"action": "volume_up"},
            "volume down": {"action": "volume_down"},
            "mute": {"action": "volume_mute"},
        }
        
        for cmd_phrase, cmd_data in system_commands.items():
            if cmd_phrase in command:
                return cmd_data
        
        return None
    
    async def _execute_system_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system control command using helper"""
        
        action = command_data["action"]
        
        # Use system control helper for better UAC handling
        if action == "shutdown":
            delay = command_data.get("delay", 30)
            result = system_helper.safe_shutdown(delay)
        elif action == "restart":
            delay = command_data.get("delay", 30)
            result = system_helper.safe_restart(delay)
        elif action == "sleep":
            result = system_helper.sleep_computer()
        elif action == "lock":
            result = system_helper.lock_computer()
        elif action == "show_desktop":
            import pyautogui
            pyautogui.hotkey('win', 'd')
            result = {"success": True, "action": "show_desktop"}
        elif action == "minimize_window":
            import pyautogui
            pyautogui.hotkey('win', 'down')
            result = {"success": True, "action": "minimize"}
        elif action == "maximize_window":
            import pyautogui
            pyautogui.hotkey('win', 'up')
            result = {"success": True, "action": "maximize"}
        elif action == "close_window":
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            result = {"success": True, "action": "close"}
        elif action in ("media_play_pause", "media_next", "media_prev", "volume_up", "volume_down", "volume_mute"):
            # Use keyboard media keys via pyautogui / keyboard
            try:
                import pyautogui
                key_map = {
                    "media_play_pause": "playpause",
                    "media_next": "nexttrack",
                    "media_prev": "prevtrack",
                    "volume_up": "volumeup",
                    "volume_down": "volumedown",
                    "volume_mute": "volumemute",
                }
                pyautogui.press(key_map[action])
                result = {"success": True, "action": action}
            except Exception:
                try:
                    import keyboard  # type: ignore
                    combo_map = {
                        "media_play_pause": "play/pause media",
                        "media_next": "next track",
                        "media_prev": "previous track",
                        "volume_up": "volume up",
                        "volume_down": "volume down",
                        "volume_mute": "mute",
                    }
                    keyboard.send(combo_map[action])
                    result = {"success": True, "action": action}
                except Exception as e:
                    result = {"success": False, "error": str(e)}
        else:
            result = {"success": False, "error": "Unknown system command"}
        
        return result
    
    async def _execute_direct_command(self, command: str) -> Dict[str, Any]:
        """Execute command directly as shell command"""
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "action": "direct_command",
                "command": command,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def search_files(self, query: str, location: str = "desktop") -> List[str]:
        """Search for files in specified location"""
        
        search_path = self.common_paths.get(location, self.common_paths["desktop"])
        
        matches = []
        for root, dirs, files in os.walk(search_path):
            for filename in files:
                if query.lower() in filename.lower():
                    matches.append(os.path.join(root, filename))
                    if len(matches) >= 10:  # Limit results
                        return matches
        
        return matches


# Tool instance
tool_instance = VoiceCommandExecutor()

