"""
System information and monitoring API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException
from loguru import logger

from models.schemas import SystemInfo, ProviderInfo, ToolInfo
from core.llm_engine import llm_engine
from core.tool_manager import tool_manager
from tools.hardware_monitor import get_system_info
from config import settings, PROVIDERS, TOOLS_CONFIG

router = APIRouter()


@router.get("/info", response_model=SystemInfo)
async def get_system_info_endpoint():
    """Get current system information"""
    try:
        info = await get_system_info()
        
        # Transform nested structure to flat structure for SystemInfo model
        transformed = {
            "cpu_percent": info.get("cpu", {}).get("usage_percent", 0.0),
            "memory_percent": info.get("memory", {}).get("virtual", {}).get("percent", 0.0),
            "disk_percent": info.get("disk", {}).get("partitions", [{}])[0].get("percent", 0.0) if info.get("disk", {}).get("partitions") else 0.0,
            "network_sent": int(info.get("network", {}).get("total", {}).get("sent_mb", 0) * 1024 * 1024),
            "network_recv": int(info.get("network", {}).get("total", {}).get("recv_mb", 0) * 1024 * 1024),
            "gpu_info": info.get("gpu", {}).get("gpus", []) if info.get("gpu") else None,
            "temperature": info.get("temperature")
        }
        
        return SystemInfo(**transformed)
    except Exception as e:
        logger.error(f"Error getting system info: {{error}}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=List[ProviderInfo])
async def get_providers():
    """Get available LLM providers (Groq only)"""
    providers = []
    
    for name, config in PROVIDERS.items():
        # Check if Groq API key is configured
        available = bool(settings.groq_api_key)
        
        providers.append(ProviderInfo(
            name=name,
            models=config["models"],
            available=available,
            supports_streaming=config["supports_streaming"],
            supports_function_calling=config["supports_function_calling"]
        ))
    
    return providers


@router.get("/tools", response_model=List[ToolInfo])
async def get_tools():
    """Get available tools"""
    tools = []
    
    for name, config in TOOLS_CONFIG.items():
        tools.append(ToolInfo(
            name=name,
            description=config["description"],
            enabled=config["enabled"],
            capabilities=config.get("capabilities", config.get("methods", []))
        ))
    
    return tools


@router.get("/status")
async def get_status():
    """Get overall system status"""
    return {
        "status": "online",
        "version": "1.0.0",
        "server": {
            "host": settings.server_host,
            "port": settings.server_port
        },
        "llm": {
            "provider": "groq",
            "model": settings.default_model,
            "api_configured": bool(settings.groq_api_key)
        },
        "tools": {
            name: config["enabled"]
            for name, config in TOOLS_CONFIG.items()
        },
        "memory": {
            "vector_enabled": settings.enable_vector_memory,
            "max_history": settings.max_conversation_history
        }
    }


@router.get("/health")
async def health_check():
    """Detailed health check"""
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check LLM engine
    try:
        llm_health = await llm_engine.health_check()
        health["checks"]["llm_engine"] = llm_health
    except Exception as e:
        health["checks"]["llm_engine"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    # Check tool manager
    try:
        tools_health = tool_manager.health_check()
        health["checks"]["tools"] = tools_health
    except Exception as e:
        health["checks"]["tools"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    return health

