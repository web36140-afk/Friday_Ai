"""
File Operations Tool
Read, write, analyze, search files and directories
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import aiofiles
import chardet
from loguru import logger

from core.tool_manager import BaseTool


class FileOperationsTool(BaseTool):
    """File operations tool"""
    
    name = "file_operations"
    description = "Read, write, analyze files and directories"
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute file operation"""
        operations = {
            "read": self.read_file,
            "write": self.write_file,
            "list": self.list_directory,
            "search": self.search_files,
            "analyze": self.analyze_file,
            "delete": self.delete_file,
            "move": self.move_file,
            "copy": self.copy_file,
            "exists": self.check_exists,
            "info": self.get_file_info
        }
        
        if operation not in operations:
            return {"error": f"Unknown operation: {operation}"}
        
        try:
            result = await operations[operation](**kwargs)
            return result
        except Exception as e:
            logger.error(f"File operation error: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def read_file(self, path: str, encoding: str = None) -> Dict[str, Any]:
        """Read file contents"""
        file_path = Path(path)
        
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        
        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}
        
        # Detect encoding if not specified
        if encoding is None:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'
        
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
            
            return {
                "success": True,
                "path": str(file_path),
                "content": content,
                "size": file_path.stat().st_size,
                "encoding": encoding
            }
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    async def write_file(
        self,
        path: str,
        content: str,
        encoding: str = 'utf-8',
        mode: str = 'w'
    ) -> Dict[str, Any]:
        """Write file contents"""
        file_path = Path(path)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(file_path, mode, encoding=encoding) as f:
                await f.write(content)
            
            return {
                "success": True,
                "path": str(file_path),
                "size": file_path.stat().st_size
            }
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}
    
    async def list_directory(
        self,
        path: str = ".",
        recursive: bool = False,
        pattern: str = "*"
    ) -> Dict[str, Any]:
        """List directory contents"""
        dir_path = Path(path)
        
        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}
        
        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}"}
        
        try:
            files = []
            directories = []
            
            if recursive:
                items = dir_path.rglob(pattern)
            else:
                items = dir_path.glob(pattern)
            
            for item in items:
                info = {
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime
                }
                
                if item.is_file():
                    files.append(info)
                elif item.is_dir():
                    directories.append(info)
            
            return {
                "success": True,
                "path": str(dir_path),
                "files": files,
                "directories": directories,
                "total_files": len(files),
                "total_directories": len(directories)
            }
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}
    
    async def search_files(
        self,
        path: str = ".",
        pattern: str = "*",
        content_search: str = None
    ) -> Dict[str, Any]:
        """Search for files"""
        dir_path = Path(path)
        
        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}
        
        try:
            results = []
            
            for file_path in dir_path.rglob(pattern):
                if file_path.is_file():
                    match_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size
                    }
                    
                    # Search file content if specified
                    if content_search:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if content_search.lower() in content.lower():
                                    match_info["content_match"] = True
                                    results.append(match_info)
                        except:
                            pass
                    else:
                        results.append(match_info)
            
            return {
                "success": True,
                "results": results,
                "total_matches": len(results)
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def analyze_file(self, path: str) -> Dict[str, Any]:
        """Analyze file (type, structure, statistics)"""
        file_path = Path(path)
        
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        
        try:
            stat = file_path.stat()
            
            analysis = {
                "success": True,
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir()
            }
            
            # Additional analysis for text files
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        analysis["lines"] = len(content.split('\n'))
                        analysis["words"] = len(content.split())
                        analysis["characters"] = len(content)
                except:
                    pass
            
            return analysis
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete file or directory"""
        file_path = Path(path)
        
        if not file_path.exists():
            return {"error": f"Path not found: {path}"}
        
        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            
            return {
                "success": True,
                "path": str(file_path),
                "message": "Deleted successfully"
            }
        except Exception as e:
            return {"error": f"Delete failed: {str(e)}"}
    
    async def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move file or directory"""
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            return {"error": f"Source not found: {source}"}
        
        try:
            shutil.move(str(src_path), str(dst_path))
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path)
            }
        except Exception as e:
            return {"error": f"Move failed: {str(e)}"}
    
    async def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy file or directory"""
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            return {"error": f"Source not found: {source}"}
        
        try:
            if src_path.is_file():
                shutil.copy2(str(src_path), str(dst_path))
            elif src_path.is_dir():
                shutil.copytree(str(src_path), str(dst_path))
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path)
            }
        except Exception as e:
            return {"error": f"Copy failed: {str(e)}"}
    
    async def check_exists(self, path: str) -> Dict[str, Any]:
        """Check if path exists"""
        file_path = Path(path)
        
        return {
            "success": True,
            "path": str(file_path),
            "exists": file_path.exists(),
            "is_file": file_path.is_file() if file_path.exists() else False,
            "is_dir": file_path.is_dir() if file_path.exists() else False
        }
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed file information"""
        return await self.analyze_file(path)

