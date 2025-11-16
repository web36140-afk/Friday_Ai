from typing import Optional, Tuple
from loguru import logger
from functools import lru_cache
import base64
import io

from config import settings


class LocalTTSUnavailable(Exception):
    pass


class CoquiLocalTTS:
    def __init__(self):
        try:
            from TTS.api import TTS  # type: ignore
        except Exception as e:
            raise LocalTTSUnavailable(f"Coqui TTS not available: {e}")

        # Use XTTS v2 multi-lingual if available, else any small fallback
        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        try:
            self.tts = TTS(model_name)
            logger.success("✓ Coqui TTS (XTTS v2) loaded")
        except Exception as e:
            logger.error(f"Failed to load XTTS v2: {e}")
            raise LocalTTSUnavailable(e)

    @staticmethod
    def to_data_url(wav_bytes: bytes) -> str:
        b64 = base64.b64encode(wav_bytes).decode("utf-8")
        return f"data:audio/wav;base64,{b64}"

    @lru_cache(maxsize=128)
    def synth_to_wav_cached(self, text: str, language: str, speaker: Optional[str]) -> bytes:
        # Generate audio bytes to memory
        wav_io = io.BytesIO()
        # XTTS supports language codes and speaker
        try:
            self.tts.tts_to_file(
                text=text,
                file_path=wav_io,
                speaker=speaker or None,
                language=language or "en"
            )
        except TypeError:
            # Some versions require explicit bytes write
            audio = self.tts.tts(text=text, speaker=speaker or None, language=language or "en")
            import soundfile as sf  # lightweight
            sf.write(wav_io, audio, 22050, format="WAV")
        return wav_io.getvalue()

    def synthesize(self, text: str, language: str = "en", speaker: Optional[str] = None) -> str:
        audio_bytes = self.synth_to_wav_cached(text, language, speaker)
        return self.to_data_url(audio_bytes)


_coqui_instance: Optional[CoquiLocalTTS] = None


def get_local_tts() -> CoquiLocalTTS:
    global _coqui_instance
    if _coqui_instance is not None:
        return _coqui_instance
    if not settings.enable_local_tts:
        raise LocalTTSUnavailable("Local TTS disabled by config")
    _coqui_instance = CoquiLocalTTS()
    return _coqui_instance


