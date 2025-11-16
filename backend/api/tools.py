"""
Tools API - Execute tools based on user commands
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from loguru import logger

from core.tool_manager import tool_manager

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolExecutionRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    operation: Optional[str] = Field(None, description="Operation to perform")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolExecutionResponse(BaseModel):
    success: bool
    tool_name: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(request: ToolExecutionRequest):
    """
    Execute a tool with given arguments
    """
    try:
        logger.info(f"🔧 Executing tool: {request.tool_name}")
        
        # Ensure tool manager is initialized
        if not tool_manager.initialized:
            tool_manager.initialize()
        
        # Build arguments
        args = request.arguments.copy()
        if request.operation:
            args["operation"] = request.operation
        
        # Execute tool
        result = await tool_manager.execute_tool(request.tool_name, args)
        
        if result.get("success", False):
            logger.success(f"✓ Tool {request.tool_name} executed successfully")
            return ToolExecutionResponse(
                success=True,
                tool_name=request.tool_name,
                result=result
            )
        else:
            logger.warning(f"✗ Tool {request.tool_name} failed: {result.get('error')}")
            return ToolExecutionResponse(
                success=False,
                tool_name=request.tool_name,
                error=result.get("error", "Unknown error")
            )
    
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_tools():
    """
    Get list of available tools
    """
    try:
        if not tool_manager.initialized:
            tool_manager.initialize()
        
        tools = tool_manager.get_available_tools()
        
        return {
            "success": True,
            "total": len(tools),
            "tools": tools
        }
    
    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def tools_health():
    """
    Check tool system health
    """
    try:
        if not tool_manager.initialized:
            tool_manager.initialize()
        
        health = tool_manager.health_check()
        
        return health
    
    except Exception as e:
        logger.error(f"Tool health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

