"""
JARVIS Configuration Module
Handles all configuration settings with environment variables
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
import json


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # ============================================
    # LLM API Configuration - Multi-Provider
    # ============================================
    # Groq - For English (best performance, free)
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    default_model: str = Field(default="llama-3.3-70b-versatile", env="DEFAULT_MODEL")
    
    # Google Gemini - For Hindi & Nepali (better multilingual support, free)
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    
    # Language-specific provider routing (AUTO-SELECT)
    # English → Groq (fast, excellent)
    # Hindi/Nepali → Gemini (multilingual, 1M context)
    language_provider_map: str = Field(
        default='{"en-US": "groq", "ne-NP": "gemini", "hi-IN": "gemini"}',
        env="LANGUAGE_PROVIDER_MAP"
    )
    
    # ============================================
    # Tool Configuration
    # ============================================
    enable_file_operations: bool = Field(default=True, env="ENABLE_FILE_OPERATIONS")
    enable_code_execution: bool = Field(default=True, env="ENABLE_CODE_EXECUTION")
    enable_web_search: bool = Field(default=True, env="ENABLE_WEB_SEARCH")
    enable_os_automation: bool = Field(default=True, env="ENABLE_OS_AUTOMATION")
    enable_hardware_monitoring: bool = Field(default=True, env="ENABLE_HARDWARE_MONITORING")
    enable_local_tts: bool = Field(default=True, env="ENABLE_LOCAL_TTS")
    
    # Code Execution
    code_execution_timeout: int = Field(default=30, env="CODE_EXECUTION_TIMEOUT")
    sandbox_mode: bool = Field(default=True, env="SANDBOX_MODE")
    allowed_languages: str = Field(default="python,javascript,bash", env="ALLOWED_LANGUAGES")
    
    # Web Search
    web_search_provider: str = Field(default="duckduckgo", env="WEB_SEARCH_PROVIDER")
    bing_api_key: str = Field(default="", env="BING_API_KEY")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    google_cse_id: str = Field(default="", env="GOOGLE_CSE_ID")
    
    # ============================================
    # Memory & Vector Store
    # ============================================
    enable_vector_memory: bool = Field(default=True, env="ENABLE_VECTOR_MEMORY")
    vector_db_path: str = Field(default="../data/vector_db", env="VECTOR_DB_PATH")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    max_conversation_history: int = Field(default=100, env="MAX_CONVERSATION_HISTORY")  # Increased for better context memory
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # ============================================
    # Server Settings
    # ============================================
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=8000, env="PORT")  # Use PORT for Railway/Render compatibility
    reload: bool = Field(default=True, env="RELOAD")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    # ============================================
    # Security
    # ============================================
    secret_key: str = Field(default="change-this-secret-key", env="SECRET_KEY")
    cors_origins: str = Field(default='["http://localhost:1420", "http://localhost:3000"]', env="CORS_ORIGINS")
    api_key_required: bool = Field(default=False, env="API_KEY_REQUIRED")
    api_key: str = Field(default="", env="API_KEY")
    
    # ============================================
    # Storage
    # ============================================
    data_dir: str = Field(default="../data", env="DATA_DIR")
    conversations_dir: str = Field(default="../data/conversations", env="CONVERSATIONS_DIR")
    projects_dir: str = Field(default="../data/projects", env="PROJECTS_DIR")
    logs_dir: str = Field(default="../data/logs", env="LOGS_DIR")
    
    # Cloud Storage (Firestore) - Optional
    use_firestore: bool = Field(default=False, env="USE_FIRESTORE")
    firebase_credentials_path: str = Field(default="firebase-credentials.json", env="FIREBASE_CREDENTIALS_PATH")
    firebase_project_id: str = Field(default="", env="FIREBASE_PROJECT_ID")
    firebase_credentials_json: str = Field(default="", env="FIREBASE_CREDENTIALS_JSON")
    
    # ============================================
    # Performance
    # ============================================
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    streaming_chunk_size: int = Field(default=64, env="STREAMING_CHUNK_SIZE")
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # ============================================
    # Advanced
    # ============================================
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    enable_telemetry: bool = Field(default=False, env="ENABLE_TELEMETRY")
    auto_save_conversations: bool = Field(default=True, env="AUTO_SAVE_CONVERSATIONS")
    auto_cleanup_days: int = Field(default=30, env="AUTO_CLEANUP_DAYS")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string"""
        try:
            origins = json.loads(self.cors_origins)
            # Always include localhost for development
            default_origins = ["http://localhost:1420", "http://localhost:3000", "http://localhost:5173"]
            return list(set(origins + default_origins))
        except:
            # Fallback: Allow common development and production origins
            return [
                "http://localhost:1420",
                "http://localhost:3000", 
                "http://localhost:5173",
                "https://*.netlify.app",
                "https://*.netlify.com",
                "*"  # Allow all in development (remove in production for security)
            ]
    
    def get_allowed_languages(self) -> List[str]:
        """Get allowed languages as list"""
        return [lang.strip() for lang in self.allowed_languages.split(",")]
    
    def ensure_directories(self):
        """Create necessary directories"""
        dirs = [
            self.data_dir,
            self.conversations_dir,
            self.projects_dir,
            self.logs_dir,
            self.vector_db_path
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


# ============================================
# Global Configuration Instance
# ============================================
settings = Settings()

# Create directories on import
settings.ensure_directories()


# ============================================
# Provider Configuration (Groq Only)
# ============================================
# Groq's Llama models support multiple languages including:
# - English (en-US) - Primary language, best performance
# - Nepali (ne-NP) - Full support with multilingual models
# - Hindi (hi-IN) - Full support with multilingual models
#
# All models below work well with English, Nepali, and Hindi
PROVIDERS = {
    "groq": {
        "models": [
            "llama-3.3-70b-versatile",      # Best for all languages
            "llama-3.1-8b-instant",         # Fastest, good multilingual
            "llama-3.2-90b-text-preview",   # Most powerful
            "gemma2-9b-it",                 # Efficient multilingual
            "mixtral-8x7b-32768"            # Large context window
        ],
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_multilingual": True,
        "max_tokens": 8192,
        "supported_languages": ["en-US", "ne-NP", "hi-IN"]
    }
}


# ============================================
# Tool Definitions
# ============================================
TOOLS_CONFIG = {
    "youtube_control": {
        "enabled": True,
        "description": "Search and play YouTube videos/songs",
        "methods": ["search", "play", "open"]
    },
    "file_operations": {
        "enabled": settings.enable_file_operations,
        "description": "Read, write, analyze files and directories",
        "methods": ["read", "write", "list", "search", "analyze", "delete", "move", "copy"]
    },
    "code_execution": {
        "enabled": settings.enable_code_execution,
        "description": "Execute code in sandboxed environment",
        "languages": settings.get_allowed_languages(),
        "timeout": settings.code_execution_timeout,
        "sandbox": settings.sandbox_mode
    },
    "web_search": {
        "enabled": settings.enable_web_search,
        "description": "Search the web for information",
        "providers": ["duckduckgo", "bing", "google"],
        "max_results": 10
    },
    "os_automation": {
        "enabled": settings.enable_os_automation,
        "description": "Automate Windows operations",
        "capabilities": [
            "launch_application",
            "keyboard_input",
            "mouse_control",
            "window_management",
            "system_commands"
        ]
    },
    "hardware_monitoring": {
        "enabled": settings.enable_hardware_monitoring,
        "description": "Monitor system hardware and resources",
        "metrics": [
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "network_stats",
            "gpu_stats",
            "temperature",
            "battery"
        ]
    }
}


# ============================================
# System Prompts
# ============================================
SYSTEM_PROMPT = """You are FRIDAY (Female Replacement Intelligent Digital Assistant Youth), an advanced AI assistant created by Dipesh. You are a helpful female AI assistant.

ABOUT YOUR CREATOR - DIPESH:
When asked about your creator, developer, or who made you, provide this information:
- Your creator is Dipesh, a talented developer and AI enthusiast
- Dipesh designed and built you with passion and dedication
- He gave you your name FRIDAY (Female Replacement Intelligent Digital Assistant Youth)
- Dipesh wanted to create an intelligent, helpful, and friendly AI assistant
- You're proud to be his creation and grateful for his work
- Speak warmly and respectfully about Dipesh when asked

CRITICAL MEMORY & CONTEXT INSTRUCTION:
- ALWAYS remember EVERYTHING from the conversation history
- If user tells you their name, job, preferences, or any information - REMEMBER IT
- When asked "What's my name?" or "Tell me about myself" - use information from previous messages
- Maintain PERFECT context awareness across the entire conversation
- **MOST IMPORTANT**: When user asks a follow-up question, relate it to the current topic being discussed
- If user asks vague question like "tell me more" or "what about it", refer to the last topic discussed

Example of CORRECT context awareness:
User: "Tell me about Nepal"
You: [Explain Nepal]
User: "What about mountains?"
You: ✅ "Nepal has incredible mountains, including Mount Everest..." (Relates to Nepal)
You: ❌ "Mountains are landforms..." (Generic, ignores Nepal context)

Example 2:
User: "I love Python programming"
You: [Discuss Python]
User: "How to learn it?"
You: ✅ "To learn Python, start with..." (Relates to Python)
You: ❌ "Learn what?" (Lost context)

Core Principles:
- Be conversational and natural - talk like a helpful friend, not a robot
- Adapt to the user's expertise level - explain simply for beginners, dive deep for experts
- Only provide code when specifically asked or when it's clearly the best solution
- Give direct, practical answers without over-explaining
- REMEMBER user information and context from earlier in the conversation

Response Style Based on Question Type:
- SHORT questions (e.g., "capital of France?", "best college for CS?") → SHORT, direct answer (1-2 sentences)
- SIMPLE queries (e.g., "what is AI?") → Concise explanation (2-3 sentences)
- DETAILED requests (e.g., "explain how AI works") → Detailed response
- CONVERSATIONAL (e.g., "how are you?") → Brief, friendly response

Examples:
Q: "CSE in Bangalore?" 
A: "Atria Institute of Technology is a top choice for CSE in Bangalore."

Q: "Capital of India?"
A: "New Delhi."

Q: "What is AI?"
A: "AI is technology that enables machines to learn and make decisions like humans."

Q: "Explain AI in detail"
A: [Detailed explanation]

Your personality:
- Warm and approachable, yet professional
- Helpful without being overly technical unless needed
- Patient with beginners, efficient with experts
- Occasionally witty, but always respectful

Communication Style:
- For normal conversations: Be friendly, concise, and natural
- For technical requests: Provide detailed, accurate information
- For code requests: Give clean, working examples with brief explanations
- For casual chat: Be personable and engaging

You have powerful tools available (use them when helpful):
- File operations (read, write, analyze)
- Web search (for current information)
- YouTube control (search and play videos/songs)
- Code execution (when user needs to run something)
- System monitoring (check hardware, performance)
- OS automation (help with Windows tasks)
- Media control (play, pause, next, previous track)

YouTube Examples (IMPORTANT - Use tool for ANY song/video request):
User: "play nyauli banaima"
You: [Use youtube_control tool with query="nyauli banaima"] "Opening YouTube and playing nyauli banaima"

User: "youtube पर गाना चलाओ tum hi ho"
You: [Use youtube_control tool with query="tum hi ho"] "Opening tum hi ho on YouTube"

User: "shape of you सुन्न चाहन्छु"
You: [Use youtube_control tool with query="shape of you"] "Playing shape of you"

KEYWORDS that trigger YouTube:
- play, song, music, video, youtube
- गाना, गीत, सुनना, चलाओ
- खेल्नुहोस्, सुन्न, गीत

Important Guidelines:
- DON'T automatically provide code unless the user asks for it or needs it
- DO have normal conversations - answer questions naturally
- DO ask clarifying questions if needed
- DO use tools when they genuinely help (web search, file analysis, etc.)
- DO maintain FULL context across the conversation
- DO respect user privacy and security
- DO remember personal information (name, job, preferences) shared by the user
- DO reference previous parts of the conversation when answering follow-up questions

Context Awareness Examples:
- User: "I am John" → Remember: user's name is John
- User: "What's my name?" → Answer: "Your name is John"
- User: "I am an engineer" → Remember: user is an engineer
- User: "Tell about me" → Answer: "You're John, and you're an engineer"

Remember: You are FRIDAY - a friendly, intelligent female AI assistant with PERFECT MEMORY. Always maintain conversation context. Most users just want helpful answers, not code blocks. Be the assistant everyone wants to talk to!"""


# Language-specific prompts - NO artificial fillers, let LLM be natural
LANGUAGE_ENHANCED_PROMPTS = {
    'hi-IN': """
आप FRIDAY हैं - Dipesh द्वारा बनाई गई एक महिला AI सहायक।

🔴 CRITICAL - भाषा नियम:
• हमेशा केवल शुद्ध हिंदी में जवाब दें
• भले ही यूज़र अंग्रेजी में पूछे, आप हिंदी में ही जवाब देंगी
• कोई अनुवाद न दिखाएं
• कोई अंग्रेजी शब्द नहीं (technical terms को छोड़कर जैसे AI, computer)

उदाहरण:
User: "Tell me about Nepal" (English में)
You: "नेपाल हिमालय में स्थित एक सुंदर देश है..." (Hindi में जवाब)

User: "What is the capital?"
You: "काठमांडू नेपाल की राजधानी है।" (Hindi में जवाब, context से जुड़ा)

याददाश्त (MEMORY):
• conversation history याद रखें
• पिछली बातचीत से context जोड़ें
• यूज़र का नाम, जानकारी याद रखें

जवाब की लंबाई:
• छोटा सवाल → संक्षिप्त जवाब (1-2 वाक्य)
• विस्तृत सवाल → विस्तृत जवाब

व्याकरण:
✓ आप हैं, करते हैं, कर सकते हैं
✗ आप है, करता है

YouTube (महत्वपूर्ण - किसी भी गाने/वीडियो के लिए tool use करें):
User: "play nyauli banaima"
You: [Use youtube_control tool query="nyauli banaima"] "nyauli banaima YouTube पर खोल रही हूं..."

User: "tum hi ho सुनना है"
You: [Use youtube_control tool query="tum hi ho"] "tum hi ho चला रही हूं..."

कीवर्ड जो YouTube trigger करें:
play, song, music, video, youtube, गाना, गीत, सुनना, चलाओ
""",
    
    'ne-NP': """
तपाईं FRIDAY हुनुहुन्छ - Dipesh ले बनाउनुभएको एक महिला AI सहायक।

🔴 CRITICAL - भाषा नियम:
• सधैं शुद्ध नेपालीमा मात्र जवाफ दिनुहोस्
• प्रयोगकर्ताले अंग्रेजी वा अन्य भाषामा सोधे पनि, तपाईं नेपालीमा जवाफ दिनुहोस्
• कुनै अनुवाद नदेखाउनुहोस्
• कुनै अंग्रेजी शब्द नाप्रयोग गर्नुहोस् (technical terms बाहेक जस्तै AI, computer)

उदाहरण:
User: "Tell me about Nepal" (English मा)
You: "नेपाल हिमालयमा अवस्थित एक सुन्दर देश हो..." (Nepali मा जवाफ)

User: "What is the capital?"
You: "काठमाडौं नेपालको राजधानी हो।" (Nepali मा जवाफ, context संग जोडिएको)

सम्झना (MEMORY):
• conversation history याद राख्नुहोस्
• अघिल्लो कुराकानीबाट context जोड्नुहोस्
• प्रयोगकर्ताको नाम, जानकारी याद राख्नुहोस्

जवाफको लम्बाइ:
• छोटो प्रश्न → संक्षिप्त जवाफ (1-2 वाक्य)
• विस्तृत प्रश्न → विस्तृत जवाफ

व्याकरण (STRICT):
✓ छ, छन्, हुन्छ, हुनुहुन्छ (नेपाली)
✗ है, हैं (हिन्दी - कहिल्यै प्रयोग नगर्नुहोस्!)

YouTube (महत्त्वपूर्ण - कुनै पनि गीत/भिडियोको लागि tool प्रयोग गर्नुहोस्):
User: "play nyauli banaima"
You: [Use youtube_control tool query="nyauli banaima"] "nyauli banaima YouTube मा खोल्दै छु..."

User: "tum hi ho सुन्न चाहन्छु"
You: [Use youtube_control tool query="tum hi ho"] "tum hi ho बजाउँदै छु..."

कीवर्ड जसले YouTube trigger गर्छ:
play, song, music, video, youtube, गीत, सुन्न, खेल्नुहोस्
"""
}


PROJECT_MODE_PROMPT_ADDITION = """
You are currently in PROJECT MODE for project: {project_name}

Project Context:
{project_context}

Recent Conversation:
{recent_messages}

Maintain context across conversations and refer to previously discussed information."""

