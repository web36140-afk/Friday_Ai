"""
Web Search Tool
Search the web using multiple providers
"""
from typing import Dict, Any, List
import asyncio
from loguru import logger

from core.tool_manager import BaseTool
from config import settings


class WebSearchTool(BaseTool):
    """Web search tool with multiple providers"""
    
    name = "web_search"
    description = "Search the web for information"
    
    async def execute(
        self,
        query: str,
        provider: str = None,
        max_results: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute web search"""
        provider = provider or settings.web_search_provider
        
        search_methods = {
            "duckduckgo": self.search_duckduckgo,
            "bing": self.search_bing,
            "google": self.search_google
        }
        
        if provider not in search_methods:
            return {
                "error": f"Unknown provider: {provider}",
                "available": list(search_methods.keys())
            }
        
        try:
            results = await search_methods[provider](query, max_results)
            return {
                "success": True,
                "query": query,
                "provider": provider,
                "results": results,
                "total": len(results)
            }
        except Exception as e:
            logger.error(f"Web search error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "provider": provider
            }
    
    async def search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                for result in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": "duckduckgo"
                    })
            
            return results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise
    
    async def search_bing(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Bing (requires API key)"""
        if not settings.bing_api_key:
            raise ValueError("Bing API key not configured")
        
        try:
            import requests
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": settings.bing_api_key}
            params = {
                "q": query,
                "count": max_results,
                "textDecorations": True,
                "textFormat": "HTML"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "bing"
                })
            
            return results
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            raise
    
    async def search_google(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Google Custom Search (requires API key)"""
        if not settings.google_api_key or not settings.google_cse_id:
            raise ValueError("Google API key or CSE ID not configured")
        
        try:
            import requests
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": settings.google_api_key,
                "cx": settings.google_cse_id,
                "q": query,
                "num": min(max_results, 10)  # Google limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "google"
                })
            
            return results
        except Exception as e:
            logger.error(f"Google search error: {e}")
            raise
    
    def validate_args(self, query: str = None, **kwargs) -> bool:
        """Validate arguments"""
        return bool(query)

