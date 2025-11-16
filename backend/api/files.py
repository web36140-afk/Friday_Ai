"""
File upload and processing API endpoints
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from tools.document_processor import process_uploaded_file
from config import settings

router = APIRouter()

# Upload directory
UPLOAD_DIR = Path(settings.data_dir) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file"""
    try:
        # Validate file type
        allowed_extensions = {
            '.pdf', '.docx', '.doc',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp',
            '.txt', '.md', '.py', '.js', '.json', '.csv', '.html', '.css'
        }
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {unique_filename}")
        
        # Process file
        result = await process_uploaded_file(str(file_path))
        
        return {
            "success": True,
            "message": "File uploaded and processed successfully",
            "file": {
                "original_name": file.filename,
                "stored_name": unique_filename,
                "path": str(file_path),
                "size_bytes": len(content),
                "type": file_ext
            },
            "processed_data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File upload error: {error}", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uploads")
async def list_uploads(limit: int = 50):
    """List uploaded files"""
    try:
        files = []
        
        if UPLOAD_DIR.exists():
            for file_path in sorted(UPLOAD_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_kb": stat.st_size / 1024,
                        "modified": stat.st_mtime,
                        "extension": file_path.suffix
                    })
        
        return {
            "success": True,
            "files": files,
            "total": len(files)
        }
    except Exception as e:
        logger.error("Error listing uploads: {error}", error=str(e))
        return {"success": False, "error": str(e), "files": []}


@router.delete("/uploads/{filename}")
async def delete_upload(filename: str):
    """Delete uploaded file"""
    try:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check - make sure file is in uploads directory
        if not str(file_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        os.remove(file_path)
        logger.info(f"Deleted file: {filename}")
        
        return {"success": True, "message": f"File {filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting file: {error}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_file(file_path: str, operation: str = "read"):
    """Process an existing file"""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        result = await process_uploaded_file(file_path)
        
        return {
            "success": True,
            "file": file_path,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing file: {error}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

