"""
Project management API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException
from loguru import logger

from models.schemas import Project, ProjectCreate, ProjectUpdate
from core.memory import memory_manager

router = APIRouter()


@router.post("/", response_model=Project)
async def create_project(request: ProjectCreate):
    """Create new project"""
    try:
        project = await memory_manager.create_project(
            name=request.name,
            description=request.description,
            initial_context=request.initial_context
        )
        logger.info(f"Created project: {project.name} ({project.id})")
        return project
    except Exception as e:
        logger.error("Error creating project: {error}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project by ID"""
    project = await memory_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, request: ProjectUpdate):
    """Update project"""
    try:
        project = await memory_manager.update_project(
            project_id=project_id,
            name=request.name,
            description=request.description,
            context=request.context,
            metadata=request.metadata
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        logger.info(f"Updated project: {project_id}")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating project: {error}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete project"""
    success = await memory_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"Deleted project: {project_id}")
    return {"message": "Project deleted successfully"}


@router.get("/", response_model=List[Project])
async def list_projects(limit: int = 100):
    """List all projects"""
    projects = await memory_manager.list_projects(limit=limit)
    return projects


@router.put("/{project_id}/context")
async def update_project_context(project_id: str, context: dict):
    """Update project context"""
    try:
        project = await memory_manager.update_project(
            project_id=project_id,
            context=context
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        logger.info(f"Updated context for project: {project_id}")
        return {"message": "Context updated successfully", "project": project}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating context: {error}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

