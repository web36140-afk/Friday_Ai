from fastapi import APIRouter
from fastapi.responses import JSONResponse
from loguru import logger

router = APIRouter(prefix="/api/windows", tags=["Windows Control"])


def _ensure_pywin32():
    try:
        import win32gui  # noqa: F401
        import win32con  # noqa: F401
        import win32api  # noqa: F401
        return True
    except Exception as e:
        logger.error(f"pywin32 unavailable: {e}")
        return False


@router.post("/snap")
def snap(direction: str):
    """
    Snap active window: left, right, up (maximize), down (minimize/restore).
    """
    if not _ensure_pywin32():
        return JSONResponse({"success": False, "error": "pywin32 not available"}, status_code=400)

    import win32gui
    import win32con
    import win32api

    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return {"success": False, "error": "No foreground window"}

        # Get virtual desktop metrics
        virtual_left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        virtual_top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        virtual_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        virtual_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

        half_w = virtual_width // 2
        half_h = virtual_height // 2

        if direction == "left":
            win32gui.MoveWindow(hwnd, virtual_left, virtual_top, half_w, virtual_height, True)
        elif direction == "right":
            win32gui.MoveWindow(hwnd, virtual_left + half_w, virtual_top, half_w, virtual_height, True)
        elif direction == "up":
            # Maximize
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        elif direction == "down":
            # Restore then minimize
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        else:
            return {"success": False, "error": f"Unknown direction: {direction}"}

        return {"success": True}
    except Exception as e:
        logger.error(f"snap error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/maximize")
def maximize():
    if not _ensure_pywin32():
        return JSONResponse({"success": False, "error": "pywin32 not available"}, status_code=400)
    import win32gui, win32con  # noqa
    try:
        hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return {"success": True}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/minimize")
def minimize():
    if not _ensure_pywin32():
        return JSONResponse({"success": False, "error": "pywin32 not available"}, status_code=400)
    import win32gui, win32con  # noqa
    try:
        hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return {"success": True}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


