"""
YouTube Control Tool
Search and play YouTube videos automatically
"""
import webbrowser
import urllib.parse
import subprocess
import time
from typing import Dict, Any
from loguru import logger

from core.tool_manager import BaseTool


class YouTubeControlTool(BaseTool):
    """Control YouTube playback and search"""
    
    name = "youtube_control"
    description = "Search and play YouTube videos"
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute YouTube operation"""
        operations = {
            "search": self.search_and_play,
            "play": self.search_and_play,
            "open": self.open_youtube
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
            logger.error(f"YouTube control error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }
    
    async def search_and_play(self, query: str, autoplay: bool = True) -> Dict[str, Any]:
        """
        Search for a video on YouTube and open it
        Works with ANY language: English, Hindi, Nepali, etc.
        
        Args:
            query: Search query (song name, video title in any language)
            autoplay: Whether to autoplay (default: True)
        
        Examples:
            - "nyauli banaima" (Nepali song)
            - "tum hi ho" (Hindi song)
            - "shape of you" (English song)
        """
        try:
            # Clean query (remove extra words)
            clean_query = query.strip()
            
            # Encode query for URL (supports Unicode for Hindi/Nepali)
            encoded_query = urllib.parse.quote(clean_query)
            
            if autoplay:
                # Search and get first result URL
                search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
                
                # Open YouTube search
                webbrowser.open(search_url)
                
                logger.info(f"🎵 Opened YouTube search: {query}")
                
                # Give time for page to load, then autoplay first result
                time.sleep(2)
                
                # Use keyboard automation to click first result and play
                try:
                    import pyautogui
                    
                    # Press Tab to focus on first video
                    time.sleep(1)
                    pyautogui.press('tab', presses=3, interval=0.2)
                    
                    # Press Enter to play
                    pyautogui.press('enter')
                    
                    logger.info(f"🎵 Autoplaying first result")
                except Exception as e:
                    logger.warning(f"Autoplay failed: {e}")
            else:
                # Just open search results
                search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
                webbrowser.open(search_url)
            
            return {
                "success": True,
                "operation": "search_and_play",
                "query": query,
                "url": search_url,
                "message": f"Opening YouTube: {query}",
                "autoplay": autoplay
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def open_youtube(self, url: str = "https://www.youtube.com") -> Dict[str, Any]:
        """Open YouTube homepage or specific URL"""
        try:
            webbrowser.open(url)
            
            return {
                "success": True,
                "operation": "open",
                "url": url,
                "message": "Opened YouTube"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_args(self, operation: str = None, **kwargs) -> bool:
        """Validate arguments"""
        if operation == "search" or operation == "play":
            return "query" in kwargs
        return bool(operation)

