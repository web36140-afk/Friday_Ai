@echo off
cls
echo ========================================
echo    FRIDAY AI Assistant - Starting...
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Check if virtual environment exists
if not exist "%SCRIPT_DIR%backend\venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run INSTALL-FRIDAY.ps1 first
    echo.
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "%SCRIPT_DIR%frontend\tauri-app\node_modules\" (
    echo ERROR: Frontend dependencies not installed!
    echo Please run INSTALL-FRIDAY.ps1 first
    echo.
    pause
    exit /b 1
)

REM Kill any existing processes on ports 8000 and 1420
echo Checking for running instances...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :1420') do taskkill /F /PID %%a 2>nul
echo.

REM Start Backend
echo [1/3] Starting Backend Server...
start "FRIDAY Backend" powershell -NoExit -Command "cd '%SCRIPT_DIR%backend'; .\venv\Scripts\Activate.ps1; Write-Host 'Starting FRIDAY Backend...' -ForegroundColor Cyan; python main.py"

echo       Waiting for backend to initialize (10 seconds)...
timeout /t 10 /nobreak >nul

REM Check if backend is running
echo       Checking backend status...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 5; Write-Host '       Backend Status: ONLINE' -ForegroundColor Green } catch { Write-Host '       Backend Status: STARTING...' -ForegroundColor Yellow }"
echo.

REM Start Frontend
echo [2/3] Starting Frontend...
start "FRIDAY Frontend" powershell -NoExit -Command "cd '%SCRIPT_DIR%frontend\tauri-app'; Write-Host 'Starting FRIDAY Frontend...' -ForegroundColor Cyan; npm run dev"

echo       Waiting for frontend to build (15 seconds)...
timeout /t 15 /nobreak >nul
echo.

REM Open browser
echo [3/3] Opening FRIDAY in browser...
timeout /t 2 /nobreak >nul
start http://localhost:1420

echo.
echo ========================================
echo   FRIDAY is running!
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:1420
echo   API Docs: http://localhost:8000/docs
echo.
echo   If page doesn't load, wait 30 seconds
echo   for frontend to finish building
echo.
echo   Press Ctrl+C in the PowerShell windows
echo   to stop FRIDAY
echo.
echo ========================================
echo.
echo Press any key to close this window...
echo (Backend and Frontend will keep running)
pause >nul

