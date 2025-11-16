"""
FRIDAY AI Assistant - Main Entry Point
Female Replacement Intelligent Digital Assistant Youth
FastAPI backend server with streaming support
"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config import settings
from api import chat, projects, system, files, tools, chat_simple, chat_v2, gesture_control, ultra_gesture_api, voice_commands_api, alexa_api, opencv_gesture_api
from core.llm_engine import llm_engine
from core.memory import memory_manager
from core.tool_manager import tool_manager
from core.semantic_memory import semantic_memory
from core.langchain_memory import langchain_memory


# ============================================
# Application Setup
# ============================================
app = FastAPI(
    title="FRIDAY AI Assistant",
    description="Advanced Female AI Assistant with Multi-Language Support",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================
# CORS Configuration
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Exception Handlers
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error("Global exception: {error}", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug_mode else "An error occurred"
        }
    )


# ============================================
# Startup & Shutdown Events
# ============================================
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting FRIDAY AI Assistant (Female AI)...")
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level.upper()
    )
    logger.add(
        f"{settings.logs_dir}/jarvis_{{time}}.log",
        rotation="500 MB",
        retention="10 days",
        level="INFO"
    )
    
    # Initialize LLM engine
    logger.info("Initializing LLM engine...")
    await llm_engine.initialize()
    
    # Initialize memory manager
    logger.info("Initializing memory manager...")
    await memory_manager.initialize()
    
    # Initialize tool manager
    logger.info("Initializing tool manager...")
    tool_manager.initialize()
    
    # Initialize semantic memory (ChatGPT-level context)
    logger.info("Initializing semantic memory system...")
    try:
        semantic_memory.initialize()
        if semantic_memory.initialized:
            logger.success("✓ Semantic memory active - ChatGPT-level context enabled!")
        else:
            logger.info("ℹ️  Semantic memory unavailable - using rule-based context")
    except Exception as e:
        logger.warning(f"Semantic memory initialization failed: {e}")
    
    # Initialize LangChain memory (Advanced conversation management)
    logger.info("Initializing LangChain conversation memory...")
    try:
        langchain_memory.initialize()
        if langchain_memory.initialized:
            logger.success("✓ LangChain memory active - Advanced context management!")
        else:
            logger.info("ℹ️  LangChain unavailable - using standard memory")
    except Exception as e:
        logger.warning(f"LangChain initialization failed: {e}")
    
    # Run health check
    logger.info("Running system health check...")
    from core.health_check import print_health_report
    health = print_health_report()
    
    if health["status"] == "unhealthy":
        logger.error("⚠️  FRIDAY started with errors - some features may not work")
    elif health["status"] == "degraded":
        logger.warning("⚠️  FRIDAY started with warnings - some optional features disabled")
    else:
        logger.success("✅ FRIDAY is online and fully operational! 🎀")
    logger.info(f"📡 Server: http://{settings.server_host}:{settings.server_port}")
    logger.info(f"📚 API Docs: http://{settings.server_host}:{settings.server_port}/docs")
    logger.info(f"🤖 Provider: Groq AI")
    logger.info(f"🧠 Model: {settings.default_model}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down FRIDAY...")
    
    # Save any pending conversations
    if settings.auto_save_conversations:
        await memory_manager.save_all()
    
    logger.success("✅ Shutdown complete")


# ============================================
# Health Check
# ============================================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "FRIDAY AI Assistant",
        "version": "2.0.0",
        "status": "online",
        "gender": "female",
        "message": "Female Replacement Intelligent Digital Assistant Youth"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "provider": "groq",
        "model": settings.default_model,
        "api_configured": bool(settings.groq_api_key),
        "tools_enabled": {
            "file_operations": settings.enable_file_operations,
            "code_execution": settings.enable_code_execution,
            "web_search": settings.enable_web_search,
            "os_automation": settings.enable_os_automation,
            "hardware_monitoring": settings.enable_hardware_monitoring
        }
    }


# ============================================
# Include Routers
# ============================================
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(tools.router, tags=["Tools"])
app.include_router(chat_simple.router, prefix="/api/chat", tags=["Simple Chat"])
app.include_router(chat_v2.router, prefix="/api/chat", tags=["Chat V2"])
app.include_router(gesture_control.router, prefix="/api", tags=["Gesture Control"])
app.include_router(ultra_gesture_api.router, tags=["Ultra Gesture Control"])
app.include_router(voice_commands_api.router, tags=["Voice Commands"])
app.include_router(alexa_api.router, tags=["Alexa Features"])
app.include_router(opencv_gesture_api.router, tags=["OpenCV Gesture Control"])
from api import stt_api
app.include_router(stt_api.router, tags=["Offline STT"])

# TTS endpoint
from fastapi import Body
from core.tts_engine import tts_engine

@app.post("/api/tts")
async def text_to_speech(
    text: str = Body(..., embed=True),
    language_code: str = Body(default="en-US", embed=True),
    slow: bool = Body(default=False, embed=True)
):
    """Generate high-quality text-to-speech audio"""
    audio_data = await tts_engine.text_to_speech(text, language_code, slow)
    if audio_data:
        return {"success": True, "audio": audio_data}
    else:
        return {"success": False, "error": "TTS generation failed"}


# ============================================
# Main Entry Point
# ============================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.reload,
        log_level=settings.log_level
    )

