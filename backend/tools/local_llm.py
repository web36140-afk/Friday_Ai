from typing import Generator, List, Dict, Optional
from loguru import logger
from config import settings

try:
    from llama_cpp import Llama  # type: ignore
except Exception as e:
    Llama = None
    _import_error = e


class LocalLLMUnavailable(Exception):
    pass


_llm_instance: Optional["LocalLLM"] = None


class LocalLLM:
    def __init__(self):
        if not settings.enable_local_llm:
            raise LocalLLMUnavailable("Local LLM disabled by config")
        if Llama is None:
            raise LocalLLMUnavailable(f"llama-cpp-python not available: {_import_error}")
        if not settings.local_llm_model_path:
            raise LocalLLMUnavailable("LOCAL_LLM_MODEL_PATH is not set")

        logger.info("Loading local GGUF model (this may take a while)...")
        self.llm = Llama(
            model_path=settings.local_llm_model_path,
            n_ctx=settings.local_llm_n_ctx,
            n_threads=settings.local_llm_threads,
            n_gpu_layers=settings.local_llm_gpu_layers,
            verbose=False,
        )
        logger.success("✓ Local LLM loaded")

    def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Generator[str, None, None]:
        """
        Stream tokens from local GGUF model. Messages use OpenAI-style roles.
        """
        try:
            for out in self.llm.create_chat_completion(
                messages=messages,
                temperature=temperature,
                stream=True
            ):
                if "choices" in out and out["choices"]:
                    delta = out["choices"][0]["delta"]
                    content = delta.get("content", "")
                    if content:
                        yield content
        except Exception as e:
            logger.error(f"Local LLM stream error: {e}")
            return


def get_local_llm() -> LocalLLM:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LocalLLM()
    return _llm_instance


