"""
Voice Commands API
Handles voice command execution and natural language processing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from loguru import logger

router = APIRouter(prefix="/api/voice", tags=["voice_commands"])


class VoiceCommandRequest(BaseModel):
    command: str
    language: str = "en-US"
    context: Optional[Dict[str, Any]] = None


class FileSearchRequest(BaseModel):
    query: str
    location: str = "desktop"


@router.post("/execute")
async def execute_voice_command(request: VoiceCommandRequest):
    """
    Execute a voice command with natural language understanding
    
    Examples:
    - "open brave and then linkedin"
    - "show me my desktop"
    - "go to facebook"
    - "open calculator"
    - "shutdown computer"
    """
    try:
        from tools.voice_command_executor import tool_instance
        
        result = await tool_instance.execute(command=request.command)
        
        return {"success": True, **result}
        
    except Exception as e:
        logger.error(f"Voice command error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@router.post("/search-files")
async def search_files(request: FileSearchRequest):
    """Search for files in specified location"""
    try:
        from tools.voice_command_executor import tool_instance
        
        files = await tool_instance.search_files(
            query=request.query,
            location=request.location
        )
        
        return {
            "success": True,
            "query": request.query,
            "location": request.location,
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/supported-apps")
async def get_supported_apps():
    """Get list of supported applications"""
    try:
        from tools.voice_command_executor import tool_instance
        
        return {
            "success": True,
            "apps": list(tool_instance.app_shortcuts.keys()),
            "count": len(tool_instance.app_shortcuts)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/supported-websites")
async def get_supported_websites():
    """Get list of supported websites"""
    try:
        from tools.voice_command_executor import tool_instance
        
        return {
            "success": True,
            "websites": {k: v for k, v in tool_instance.websites.items()},
            "count": len(tool_instance.websites)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/browsers")
async def get_available_browsers():
    """Get list of detected browsers"""
    try:
        from tools.voice_command_executor import tool_instance
        
        return {
            "success": True,
            "browsers": tool_instance.browsers,
            "count": len(tool_instance.browsers)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


logger.info("🎙️ Voice Commands API loaded")

