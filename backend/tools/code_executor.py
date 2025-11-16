"""
Code Executor Tool
Safely execute code in sandboxed environment
"""
import asyncio
import sys
import io
import contextlib
from typing import Dict, Any
from loguru import logger

from core.tool_manager import BaseTool
from config import settings


class CodeExecutorTool(BaseTool):
    """Code execution tool with sandbox support"""
    
    name = "code_executor"
    description = "Execute code safely (Python, JavaScript, Bash)"
    
    async def execute(self, language: str, code: str, **kwargs) -> Dict[str, Any]:
        """Execute code"""
        language = language.lower()
        
        executors = {
            "python": self.execute_python,
            "javascript": self.execute_javascript,
            "js": self.execute_javascript,
            "bash": self.execute_bash,
            "shell": self.execute_bash,
            "cmd": self.execute_bash
        }
        
        if language not in executors:
            return {
                "error": f"Unsupported language: {language}",
                "supported": list(executors.keys())
            }
        
        if language not in settings.get_allowed_languages():
            return {"error": f"Language '{language}' is not enabled"}
        
        try:
            result = await executors[language](code)
            return result
        except Exception as e:
            logger.error(f"Code execution error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "language": language
            }
    
    async def execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code"""
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result = {
            "success": False,
            "language": "python",
            "output": "",
            "error": "",
            "return_value": None
        }
        
        try:
            # Create restricted globals/locals
            exec_globals = {
                "__builtins__": __builtins__,
                "print": print
            }
            exec_locals = {}
            
            # Redirect stdout/stderr
            with contextlib.redirect_stdout(stdout_capture):
                with contextlib.redirect_stderr(stderr_capture):
                    # Execute code
                    exec(code, exec_globals, exec_locals)
            
            # Get output
            result["output"] = stdout_capture.getvalue()
            result["error"] = stderr_capture.getvalue()
            result["success"] = True
            
            # Get return value if any
            if "_" in exec_locals:
                result["return_value"] = str(exec_locals["_"])
            
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            result["success"] = False
        
        return result
    
    async def execute_javascript(self, code: str) -> Dict[str, Any]:
        """Execute JavaScript code (requires Node.js)"""
        try:
            # Create temporary file with code
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with Node.js
            process = await asyncio.create_subprocess_exec(
                'node', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=settings.code_execution_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "language": "javascript",
                    "error": "Execution timeout"
                }
            
            # Cleanup
            import os
            os.unlink(temp_file)
            
            return {
                "success": process.returncode == 0,
                "language": "javascript",
                "output": stdout.decode(),
                "error": stderr.decode(),
                "return_code": process.returncode
            }
        
        except FileNotFoundError:
            return {
                "success": False,
                "language": "javascript",
                "error": "Node.js not found. Please install Node.js to execute JavaScript."
            }
        except Exception as e:
            return {
                "success": False,
                "language": "javascript",
                "error": str(e)
            }
    
    async def execute_bash(self, code: str) -> Dict[str, Any]:
        """Execute Bash/Shell commands"""
        try:
            # Execute with PowerShell on Windows, bash on Unix
            if sys.platform == "win32":
                shell_cmd = ['powershell', '-Command', code]
            else:
                shell_cmd = ['bash', '-c', code]
            
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=settings.code_execution_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "language": "bash",
                    "error": "Execution timeout"
                }
            
            return {
                "success": process.returncode == 0,
                "language": "bash",
                "output": stdout.decode(),
                "error": stderr.decode(),
                "return_code": process.returncode
            }
        
        except Exception as e:
            return {
                "success": False,
                "language": "bash",
                "error": str(e)
            }
    
    def validate_args(self, language: str = None, code: str = None, **kwargs) -> bool:
        """Validate arguments"""
        if not language or not code:
            return False
        return True

