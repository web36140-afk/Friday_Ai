@echo off
cls
echo ========================================
echo    FRIDAY - Status Checker
echo ========================================
echo.

echo Checking Backend (Port 8000)...
netstat -ano | findstr :8000
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend is running on port 8000
) else (
    echo [X] Backend is NOT running
)
echo.

echo Checking Frontend (Port 1420)...
netstat -ano | findstr :1420
if %ERRORLEVEL% EQU 0 (
    echo [OK] Frontend is running on port 1420
) else (
    echo [X] Frontend is NOT running
)
echo.

echo Testing Backend API...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing; Write-Host '[OK] Backend API responding' -ForegroundColor Green; $r.Content } catch { Write-Host '[X] Backend API not responding' -ForegroundColor Red }"
echo.

echo Testing Frontend...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:1420' -UseBasicParsing -TimeoutSec 2 | Out-Null; Write-Host '[OK] Frontend is accessible' -ForegroundColor Green } catch { Write-Host '[X] Frontend not accessible' -ForegroundColor Red }"
echo.

echo ========================================
echo.

echo If both are running but browser shows error:
echo 1. Wait 30 seconds for frontend to build
echo 2. Clear browser cache (Ctrl+Shift+Delete)
echo 3. Try incognito mode (Ctrl+Shift+N)
echo 4. Check console for errors (F12)
echo.

pause

