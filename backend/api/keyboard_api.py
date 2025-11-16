from fastapi import APIRouter
from fastapi.responses import JSONResponse
from loguru import logger

router = APIRouter(prefix="/api/keyboard", tags=["Keyboard"])


@router.post("/send")
def send_hotkey(combo: str):
    """
    Send a hotkey combo, e.g., 'ctrl+tab', 'ctrl+shift+p'.
    """
    try:
        import keyboard  # type: ignore
    except Exception as e:
        return JSONResponse({"success": False, "error": f"keyboard module unavailable: {e}"}, status_code=400)

    try:
        keyboard.press_and_release(combo)
        return {"success": True}
    except Exception as e:
        logger.error(f"send_hotkey error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


