"""
System Health Check
Ensures all components are working correctly
"""
from typing import Dict, Any
from loguru import logger


def check_system_health() -> Dict[str, Any]:
    """
    Comprehensive health check of all FRIDAY components
    """
    health = {
        "status": "healthy",
        "components": {},
        "warnings": [],
        "errors": []
    }
    
    # Check LLM Providers
    try:
        from config import settings
        
        if settings.groq_api_key:
            health["components"]["groq"] = "✓ Available"
        else:
            health["components"]["groq"] = "✗ API key missing"
            health["warnings"].append("Groq API key not configured")
        
        if settings.google_api_key:
            health["components"]["gemini"] = "✓ Available"
        else:
            health["components"]["gemini"] = "✗ API key missing"
            health["warnings"].append("Gemini API key missing (Hindi/Nepali won't work optimally)")
    except Exception as e:
        health["errors"].append(f"Config error: {e}")
    
    # Check NLP Components
    try:
        import nltk
        health["components"]["nltk"] = "✓ Available"
    except ImportError:
        health["components"]["nltk"] = "⚠ Optional (install for enhanced NLP)"
        health["warnings"].append("NLTK not installed - basic NLP will be used")
    
    # Check TTS
    try:
        import edge_tts
        health["components"]["tts"] = "✓ Edge TTS Available"
    except ImportError:
        health["components"]["tts"] = "✗ Missing"
        health["errors"].append("edge-tts not installed")
    
    # Check Tools
    try:
        from core.tool_manager import tool_manager
        tool_manager.initialize()
        health["components"]["tools"] = f"✓ {len(tool_manager.tools)} tools loaded"
    except Exception as e:
        health["components"]["tools"] = f"⚠ Error: {e}"
        health["warnings"].append(f"Tools initialization issue: {e}")
    
    # Check Context Tracking
    try:
        from core.context_tracker import context_tracker
        from core.smart_nlp import smart_nlp
        from core.reasoning_engine import reasoning_engine
        
        health["components"]["context_system"] = "✓ Smart context enabled"
        health["components"]["nlp_engine"] = "✓ NLP ready"
        health["components"]["reasoning"] = "✓ Chain of thought enabled"
    except Exception as e:
        health["errors"].append(f"Intelligence system error: {e}")
    
    # Overall status
    if health["errors"]:
        health["status"] = "unhealthy"
    elif health["warnings"]:
        health["status"] = "degraded"
    
    return health


def print_health_report():
    """Print formatted health report"""
    health = check_system_health()
    
    logger.info("=" * 60)
    logger.info("🏥 FRIDAY HEALTH CHECK")
    logger.info("=" * 60)
    
    logger.info(f"\n📊 Overall Status: {health['status'].upper()}")
    
    logger.info("\n🔧 Components:")
    for component, status in health["components"].items():
        logger.info(f"  {component}: {status}")
    
    if health["warnings"]:
        logger.warning("\n⚠️  Warnings:")
        for warning in health["warnings"]:
            logger.warning(f"  - {warning}")
    
    if health["errors"]:
        logger.error("\n❌ Errors:")
        for error in health["errors"]:
            logger.error(f"  - {error}")
    
    logger.info("\n" + "=" * 60)
    
    return health

