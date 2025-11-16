"""
Pydantic models for request/response schemas
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# Chat Models
# ============================================
class Message(BaseModel):
    """Chat message"""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Chat request"""
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    stream: bool = True
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    language: Optional[str] = None  # Output language name (English, Nepali, Hindi, etc.)
    language_code: Optional[str] = "en-US"  # Language code for provider routing (en-US, ne-NP, hi-IN)
    system_prompt_override: Optional[str] = None  # Override system prompt for language


class ChatResponse(BaseModel):
    """Chat response (non-streaming)"""
    response: str
    conversation_id: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    type: Literal["token", "tool_call", "tool_result", "error", "done"]
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ============================================
# Project Models
# ============================================
class Project(BaseModel):
    """Project with persistent context"""
    id: str
    name: str
    description: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    conversation_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    """Create project request"""
    name: str
    description: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    """Update project request"""
    name: Optional[str] = None
    description: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================
# Conversation Models
# ============================================
class Conversation(BaseModel):
    """Conversation history"""
    id: str
    name: Optional[str] = None
    project_id: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================
# Tool Models
# ============================================
class ToolCall(BaseModel):
    """Tool call request"""
    tool_name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Tool execution result"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None


# ============================================
# System Models
# ============================================
class SystemInfo(BaseModel):
    """System information"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    gpu_info: Optional[List[Dict[str, Any]]] = None
    temperature: Optional[Dict[str, float]] = None


class ProviderInfo(BaseModel):
    """LLM provider information"""
    name: str
    models: List[str]
    available: bool
    supports_streaming: bool
    supports_function_calling: bool


class ToolInfo(BaseModel):
    """Tool information"""
    name: str
    description: str
    enabled: bool
    capabilities: List[str]


# ============================================
# Configuration Models
# ============================================
class ConfigUpdate(BaseModel):
    """Update configuration"""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    enable_tools: Optional[Dict[str, bool]] = None

