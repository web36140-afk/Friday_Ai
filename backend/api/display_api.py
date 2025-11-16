from fastapi import APIRouter
from fastapi.responses import JSONResponse
from loguru import logger

router = APIRouter(prefix="/api/display", tags=["Display"])


@router.get("/monitors")
def get_monitors():
    """
    Return monitor geometries and virtual desktop bounds (Windows).
    """
    try:
        try:
            import win32api
            import win32con
        except Exception as e:
            return JSONResponse({"success": False, "error": f"win32api unavailable: {e}"}, status_code=400)

        monitors = []
        virtual_left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        virtual_top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        virtual_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        virtual_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

        for hMon, hDC, rect in win32api.EnumDisplayMonitors():
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top

            info = win32api.GetMonitorInfo(hMon)
            is_primary = bool(info.get("Flags", 0) == 1) or info.get("Device", "").endswith("\\DISPLAY1")

            monitors.append({
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
                "width": width,
                "height": height,
                "is_primary": is_primary,
                "device": info.get("Device", "")
            })

        return {
            "success": True,
            "monitors": monitors,
            "virtual": {
                "left": virtual_left,
                "top": virtual_top,
                "width": virtual_width,
                "height": virtual_height
            }
        }
    except Exception as e:
        logger.error(f"get_monitors error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


