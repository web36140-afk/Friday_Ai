"""
ALEXA-LIKE API ENDPOINTS
Complete voice assistant features
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from tools.alexa_features import alexa_features

router = APIRouter()


# ============================================
# REQUEST MODELS
# ============================================

class TimerRequest(BaseModel):
    duration: int  # seconds
    name: Optional[str] = "Timer"


class AlarmRequest(BaseModel):
    time: str  # e.g., "7:30 AM"
    name: Optional[str] = "Alarm"


class TodoRequest(BaseModel):
    item: str
    list_name: Optional[str] = "default"


class CompleteTodoRequest(BaseModel):
    item_text: str
    list_name: Optional[str] = "default"


class ShoppingRequest(BaseModel):
    item: str
    quantity: Optional[str] = "1"


class RoutineRequest(BaseModel):
    routine_name: str


class QuickQueryRequest(BaseModel):
    query: str


# ============================================
# TIMER ENDPOINTS
# ============================================

@router.post("/api/alexa/timer/set")
async def set_timer(request: TimerRequest):
    """Set a timer"""
    try:
        result = alexa_features.set_timer(request.duration, request.name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alexa/timer/cancel")
async def cancel_timer(timer_id: Optional[str] = None):
    """Cancel a timer"""
    try:
        result = alexa_features.cancel_timer(timer_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alexa/timers")
async def get_timers():
    """Get all active timers"""
    try:
        result = alexa_features.get_timers()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alexa/alarm/set")
async def set_alarm(request: AlarmRequest):
    """Set an alarm"""
    try:
        result = alexa_features.set_alarm(request.time, request.name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TO-DO LIST ENDPOINTS
# ============================================

@router.post("/api/alexa/todo/add")
async def add_todo(request: TodoRequest):
    """Add item to to-do list"""
    try:
        result = alexa_features.add_todo(request.item, request.list_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alexa/todo/complete")
async def complete_todo(request: CompleteTodoRequest):
    """Mark todo item as complete"""
    try:
        result = alexa_features.complete_todo(request.item_text, request.list_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alexa/todos")
async def get_todos(list_name: str = "default"):
    """Get to-do list"""
    try:
        result = alexa_features.get_todos(list_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SHOPPING LIST ENDPOINTS
# ============================================

@router.post("/api/alexa/shopping/add")
async def add_shopping_item(request: ShoppingRequest):
    """Add item to shopping list"""
    try:
        result = alexa_features.add_to_shopping_list(request.item, request.quantity)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alexa/shopping")
async def get_shopping_list():
    """Get shopping list"""
    try:
        result = alexa_features.get_shopping_list()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ROUTINE ENDPOINTS
# ============================================

@router.post("/api/alexa/routine/run")
async def run_routine(request: RoutineRequest):
    """Execute a routine"""
    try:
        result = alexa_features.run_routine(request.routine_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alexa/routines")
async def get_routines():
    """Get all available routines"""
    try:
        return {
            "success": True,
            "routines": alexa_features.routines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# QUICK QUERY ENDPOINT
# ============================================

@router.post("/api/alexa/quick")
async def quick_query(request: QuickQueryRequest):
    """Get quick answer for simple queries"""
    try:
        answer = alexa_features.quick_answer(request.query)
        if answer:
            return {
                "success": True,
                "answer": answer,
                "is_quick": True
            }
        else:
            return {
                "success": False,
                "is_quick": False,
                "message": "Needs AI processing"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PROACTIVE SUGGESTIONS
# ============================================

@router.get("/api/alexa/suggestion")
async def get_suggestion():
    """Get proactive suggestion"""
    try:
        suggestion = alexa_features.get_proactive_suggestion()
        if suggestion:
            return {
                "success": True,
                "suggestion": suggestion
            }
        else:
            return {
                "success": True,
                "suggestion": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CONTEXT MANAGEMENT
# ============================================

@router.post("/api/alexa/context/set")
async def set_context(key: str, value: Any):
    """Set conversational context"""
    try:
        alexa_features.set_context(key, value)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alexa/context/{key}")
async def get_context(key: str):
    """Get conversational context"""
    try:
        value = alexa_features.get_context(key)
        return {"success": True, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alexa/context/clear")
async def clear_context():
    """Clear conversational context"""
    try:
        alexa_features.clear_context()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

