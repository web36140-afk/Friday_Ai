from loguru import logger
from typing import Optional, List
from faster_whisper import WhisperModel
import numpy as np
import io
from pydub import AudioSegment


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
        Transcribe an audio buffer (bytes). Handles webm/ogg/wav via pydub/ffmpeg.
        Returns text.
        """
        try:
            # Decode with pydub (requires ffmpeg installed)
            audio = AudioSegment.from_file(io.BytesIO(wav_bytes))
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)  # 16-bit PCM mono 16k
            samples = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0

            segments, _ = self.model.transcribe(
                samples,
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


