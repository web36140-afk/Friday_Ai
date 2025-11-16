"""
Text-to-Speech Engine - Ultra-Natural Human-Like Voices
Using Microsoft Edge Neural TTS (FREE, same quality as Perplexity)
"""
import os
import tempfile
import base64
import asyncio
from typing import Optional
from loguru import logger
import edge_tts


class TTSEngine:
    """Text-to-Speech Engine with ultra-natural neural voices (like Perplexity)"""
    
    # Best natural voices for each language (Microsoft Edge Neural TTS)
    # Using NATIVE voices for each language
    VOICE_MAP = {
        # English - Ultra-natural neural voices
        'en-US': 'en-US-AriaNeural',        # Female, very natural English
        'en': 'en-US-GuyNeural',            # Male, natural English
        
        # Hindi - Native Hindi neural voices
        'hi-IN': 'hi-IN-SwaraNeural',       # Female, natural Hindi
        'hi': 'hi-IN-MadhurNeural',         # Male, natural Hindi
        
        # Nepali - Native Nepali neural voice (Female - Best quality)
        'ne-NP': 'ne-NP-HemkalaNeural',     # Female, NATIVE Nepali voice (BEST)
        'ne': 'ne-NP-SagarNeural'           # Male, NATIVE Nepali voice
    }
    
    def __init__(self):
        self.initialized = True
        logger.info("🎙️ TTS Engine initialized with Microsoft Edge Neural TTS (Ultra-Natural)")
        logger.info("✨ Voice quality: Human-like, same as Perplexity")
    
    def _add_natural_fillers(self, text: str, language_code: str) -> str:
        """
        DISABLE fillers - let the LLM generate natural text
        Fillers should come from the LLM itself, not added artificially
        """
        # Simply return the text as-is
        # The LLM (Gemini/Groq) already generates natural conversational text
        # Adding artificial fillers makes it sound worse
        return text
    
    async def text_to_speech(
        self,
        text: str,
        language_code: str = 'en-US',
        slow: bool = False
    ) -> Optional[str]:
        """
        Convert text to speech using Microsoft Edge Neural TTS
        Produces ultra-natural, human-like voice (same quality as Perplexity)
        
        Args:
            text: Text to convert to speech
            language_code: Language code (en-US, hi-IN, ne-NP)
            slow: Ignored (speed is natural by default)
        
        Returns:
            Base64 encoded MP3 audio data
        """
        try:
            # Add natural fillers for more human-like speech
            natural_text = self._add_natural_fillers(text, language_code)
            
            # Get the best neural voice for this language
            voice = self.VOICE_MAP.get(language_code, 'en-US-AriaNeural')
            
            logger.info(f"🎙️ Generating ultra-natural TTS: {voice} for {language_code}")
            
            # Create temp file for audio
            temp_path = tempfile.mktemp(suffix='.mp3')
            
            # Generate speech using Edge TTS (neural, human-like)
            # Use natural_text with fillers for more human sound
            # Adjust rate and pitch for ultra-natural delivery
            rate = '+0%'  # Natural speaking rate (not too fast, not too slow)
            pitch = '+0Hz'  # Natural pitch
            
            communicate = edge_tts.Communicate(
                natural_text, 
                voice,
                rate=rate,
                pitch=pitch
            )
            await communicate.save(temp_path)
            
            # Read and encode as base64
            with open(temp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            logger.success(f"✅ Generated human-like TTS: {len(audio_data)} bytes")
            return f"data:audio/mp3;base64,{audio_base64}"
        
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            return None
    
    async def get_supported_languages(self):
        """Get list of supported languages with ultra-natural NATIVE voices"""
        return {
            'en-US': {
                'name': 'English', 
                'quality': 'ultra-natural', 
                'voice': 'Aria/Guy (Neural)',
                'native': True
            },
            'hi-IN': {
                'name': 'Hindi (हिंदी)', 
                'quality': 'ultra-natural', 
                'voice': 'Swara/Madhur (Neural)',
                'native': True
            },
            'ne-NP': {
                'name': 'Nepali (नेपाली)', 
                'quality': 'ultra-natural', 
                'voice': 'Hemkala/Sagar (Neural)',
                'native': True
            }
        }
    
    async def list_available_voices(self):
        """List all available Microsoft Edge Neural voices"""
        try:
            voices = await edge_tts.list_voices()
            return voices
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []


# Global instance
tts_engine = TTSEngine()

