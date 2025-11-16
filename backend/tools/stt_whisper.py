from loguru import logger
from typing import Optional, List
from faster_whisper import WhisperModel
import numpy as np
import soundfile as sf
import io


class LocalWhisperSTT:
    """
    Offline STT using faster-whisper (CTranslate2).
    Supports small/base/small-int8/medium depending on hardware.
    """
    def __init__(self, model_size: str = "base", device: str = "auto"):
        compute_type = "int8" if "int8" in model_size else "float16"
        try:
            self.model = WhisperModel(
                model_size.replace("-int8", ""),
                device=device if device != "auto" else None,
                compute_type=compute_type
            )
            logger.success(f"✓ Local Whisper STT loaded: {model_size}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model ({model_size}): {e}")
            raise

    def transcribe_wav_bytes(self, wav_bytes: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe a full WAV audio buffer (bytes). Returns text.
        """
        try:
            data, sr = sf.read(io.BytesIO(wav_bytes))
            if sr != 16000:
                # Resample to 16k if needed
                import numpy as np
                import math
                ratio = 16000 / sr
                new_length = math.floor(len(data) * ratio)
                x = np.linspace(0, 1, len(data))
                xp = np.linspace(0, 1, new_length)
                data = np.interp(xp, x, data).astype(np.float32)
                sr = 16000
            if data.ndim > 1:
                data = np.mean(data, axis=1)  # mono

            segments, _ = self.model.transcribe(
                data,
                language=language,
                beam_size=1,
                vad_filter=True
            )
            text = "".join(seg.text for seg in segments).strip()
            return text
        except Exception as e:
            logger.error(f"STT transcribe error: {e}")
            return ""


# Global instance (lazy)
stt_engine: Optional[LocalWhisperSTT] = None


def get_stt() -> LocalWhisperSTT:
    global stt_engine
    if stt_engine is None:
        # Choose a sensible default model for offline use
        stt_engine = LocalWhisperSTT(model_size="small-int8")
    return stt_engine


