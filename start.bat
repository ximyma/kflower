@echo off
chcp 65001 >nul
title Kflower Startup

echo.
echo ========================================
echo   Kflower - Starting Services...
echo ========================================
echo.

:: Kill existing services first
echo [*] Stopping existing services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8898 " ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5111 " ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
timeout /t 1 >nul

:: Start backend
echo [*] Starting Backend (port 8898)...
start "Kflower-Backend" cmd /c "cd /d D:\kflower\kflower-backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8898"
echo [*] Waiting for backend to start...
timeout /t 3 >nul

:: Start frontend
echo [*] Starting Frontend (port 5111)...
start "Kflower-Frontend" cmd /c "cd /d D:\kflower\kflower-frontend && npm run dev"
echo [*] Waiting for frontend to start...
timeout /t 4 >nul

:: Check status
echo.
echo ========================================
echo   Checking services...
echo ========================================
netstat -ano | findstr ":8898 .*LISTENING" >nul
if %errorlevel%==0 (
    echo [OK] Backend:  http://127.0.0.1:8898
) else (
    echo [FAIL] Backend failed to start
)

netstat -ano | findstr ":5111 .*LISTENING" >nul
if %errorlevel%==0 (
    echo [OK] Frontend: http://localhost:5111
) else (
    echo [FAIL] Frontend failed to start
)

echo.
echo ========================================
echo   All services started!
echo   Frontend: http://localhost:5111
echo   Login:    admin / admin123
echo ========================================
echo.
pause
