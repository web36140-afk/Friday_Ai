"""
Weather and News Tool
Get weather information and latest news
"""
import aiohttp
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime

from core.tool_manager import BaseTool
from config import settings


class WeatherNewsTool(BaseTool):
    """Get weather and news information"""
    
    name = "weather_news"
    description = "Get weather forecast and latest news"
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute weather/news operation"""
        operations = {
            "weather": self.get_weather,
            "forecast": self.get_forecast,
            "news": self.get_news,
            "news_search": self.search_news
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
            logger.error(f"Weather/News error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }
    
    async def get_weather(self, city: str = "Bangalore", country: str = "IN") -> Dict[str, Any]:
        """Get current weather for a city"""
        try:
            # Using OpenWeatherMap API (free tier)
            # For production, get API key from: https://openweathermap.org/api
            # For now, use wttr.in (no API key needed)
            
            url = f"https://wttr.in/{city}?format=j1"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        current = data.get("current_condition", [{}])[0]
                        
                        return {
                            "success": True,
                            "city": city,
                            "country": country,
                            "temperature": current.get("temp_C", "N/A"),
                            "feels_like": current.get("FeelsLikeC", "N/A"),
                            "condition": current.get("weatherDesc", [{}])[0].get("value", "N/A"),
                            "humidity": current.get("humidity", "N/A"),
                            "wind_speed": current.get("windspeedKmph", "N/A"),
                            "wind_direction": current.get("winddir16Point", "N/A"),
                            "visibility": current.get("visibility", "N/A"),
                            "pressure": current.get("pressure", "N/A"),
                            "uv_index": current.get("uvIndex", "N/A")
                        }
                    else:
                        return {"success": False, "error": "Failed to fetch weather data"}
        
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_forecast(self, city: str = "Bangalore", days: int = 3) -> Dict[str, Any]:
        """Get weather forecast"""
        try:
            url = f"https://wttr.in/{city}?format=j1"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        forecast_data = data.get("weather", [])[:days]
                        
                        forecasts = []
                        for day in forecast_data:
                            forecasts.append({
                                "date": day.get("date"),
                                "max_temp": day.get("maxtempC"),
                                "min_temp": day.get("mintempC"),
                                "condition": day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "N/A"),
                                "humidity": day.get("hourly", [{}])[4].get("humidity"),
                                "chance_of_rain": day.get("hourly", [{}])[4].get("chanceofrain")
                            })
                        
                        return {
                            "success": True,
                            "city": city,
                            "forecasts": forecasts
                        }
                    else:
                        return {"success": False, "error": "Failed to fetch forecast data"}
        
        except Exception as e:
            logger.error(f"Forecast fetch error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_news(self, country: str = "in", category: str = "general") -> Dict[str, Any]:
        """Get latest news headlines"""
        try:
            # Using RSS feed from Google News (no API key needed)
            url = f"https://news.google.com/rss?hl=en-{country.upper()}&gl={country.upper()}&ceid={country.upper()}:en"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        import xml.etree.ElementTree as ET
                        
                        text = await response.text()
                        root = ET.fromstring(text)
                        
                        articles = []
                        for item in root.findall('.//item')[:10]:  # Get top 10 news
                            articles.append({
                                "title": item.find('title').text if item.find('title') is not None else "N/A",
                                "link": item.find('link').text if item.find('link') is not None else "N/A",
                                "published": item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
                            })
                        
                        return {
                            "success": True,
                            "country": country,
                            "category": category,
                            "total": len(articles),
                            "articles": articles
                        }
                    else:
                        return {"success": False, "error": "Failed to fetch news"}
        
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_news(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search news by topic"""
        try:
            # Use Google News search
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        import xml.etree.ElementTree as ET
                        
                        text = await response.text()
                        root = ET.fromstring(text)
                        
                        articles = []
                        for item in root.findall('.//item')[:max_results]:
                            articles.append({
                                "title": item.find('title').text if item.find('title') is not None else "N/A",
                                "link": item.find('link').text if item.find('link') is not None else "N/A",
                                "published": item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
                            })
                        
                        return {
                            "success": True,
                            "query": query,
                            "total": len(articles),
                            "articles": articles
                        }
                    else:
                        return {"success": False, "error": "Failed to search news"}
        
        except Exception as e:
            logger.error(f"News search error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_args(self, operation: str = None, **kwargs) -> bool:
        """Validate arguments"""
        return bool(operation)

