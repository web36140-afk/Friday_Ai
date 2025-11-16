@echo off
cls
echo ========================================
echo    FRIDAY - Stopping Services
echo ========================================
echo.

echo Stopping Backend (Port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo   Killing process %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo Stopping Frontend (Port 1420)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :1420') do (
    echo   Killing process %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo Closing PowerShell windows...
taskkill /FI "WINDOWTITLE eq FRIDAY Backend" /F 2>nul
taskkill /FI "WINDOWTITLE eq FRIDAY Frontend" /F 2>nul

echo.
echo ========================================
echo   All FRIDAY services stopped
echo ========================================
echo.

pause

