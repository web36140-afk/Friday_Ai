"""
Tool Manager - Central tool execution system
Manages and executes all available tools
"""
import sys
from typing import Dict, Any, List, Optional
from loguru import logger

from config import settings, TOOLS_CONFIG


class BaseTool:
    """Base class for all tools"""
    
    name: str = "base_tool"
    description: str = "Base tool"
    enabled: bool = True
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool - override in subclass"""
        raise NotImplementedError
    
    def validate_args(self, **kwargs) -> bool:
        """Validate arguments - override in subclass"""
        return True


class ToolManager:
    """Manages all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.initialized = False
    
    def initialize(self):
        """Initialize all enabled tools"""
        if self.initialized:
            return
        
        # Import and register tools
        if settings.enable_file_operations:
            from tools.file_ops import FileOperationsTool
            self.register_tool(FileOperationsTool())
            logger.success("✓ File Operations tool loaded")
        
        if settings.enable_code_execution:
            from tools.code_executor import CodeExecutorTool
            self.register_tool(CodeExecutorTool())
            logger.success("✓ Code Executor tool loaded")
        
        if settings.enable_web_search:
            from tools.web_search import WebSearchTool
            self.register_tool(WebSearchTool())
            logger.success("✓ Web Search tool loaded")
        
        if settings.enable_os_automation:
            from tools.os_automation import OSAutomationTool
            self.register_tool(OSAutomationTool())
            logger.success("✓ OS Automation tool loaded")
        
        if settings.enable_hardware_monitoring:
            from tools.hardware_monitor import HardwareMonitorTool
            self.register_tool(HardwareMonitorTool())
            logger.success("✓ Hardware Monitor tool loaded")
        
        # Windows Control Tool (volume, brightness, power)
        if sys.platform == "win32":
            from tools.windows_control import WindowsControlTool
            self.register_tool(WindowsControlTool())
            logger.success("✓ Windows Control tool loaded")
            
            # Media Control Tool (music playback)
            from tools.media_control import MediaControlTool
            self.register_tool(MediaControlTool())
            logger.success("✓ Media Control tool loaded")
            
            # YouTube Control Tool
            from tools.youtube_control import YouTubeControlTool
            self.register_tool(YouTubeControlTool())
            logger.success("✓ YouTube Control tool loaded")
        
        # Weather & News Tool
        from tools.weather_news import WeatherNewsTool
        self.register_tool(WeatherNewsTool())
        logger.success("✓ Weather & News tool loaded")
        
        # Reminders & Schedule Tool
        from tools.reminders import RemindersScheduleTool
        self.register_tool(RemindersScheduleTool())
        logger.success("✓ Reminders & Schedule tool loaded")
        
        self.initialized = True
        logger.info(f"Tool Manager initialized with {len(self.tools)} tool(s)")
    
    def register_tool(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool by name"""
        if not self.initialized:
            self.initialize()
        
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        tool = self.tools[tool_name]
        
        if not tool.enabled:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is disabled"
            }
        
        try:
            # Validate arguments
            if not tool.validate_args(**arguments):
                return {
                    "success": False,
                    "error": "Invalid arguments"
                }
            
            # Execute tool
            logger.info(f"Executing tool: {tool_name}")
            result = await tool.execute(**arguments)
            
            logger.debug(f"Tool {tool_name} completed successfully")
            return {
                "success": True,
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "enabled": tool.enabled
            }
            for tool in self.tools.values()
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of tool system"""
        return {
            "status": "healthy",
            "tools_loaded": len(self.tools),
            "tools": {
                name: {"enabled": tool.enabled}
                for name, tool in self.tools.items()
            }
        }


# Global instance
tool_manager = ToolManager()

