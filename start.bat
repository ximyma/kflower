@echo off
chcp 65001 >nul
title Kflower Startup

echo.
echo ========================================
echo   Kflower - Starting Services...
echo ========================================
echo.

REM Kill existing services
echo [*] Stopping existing services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8788 " ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
timeout /t 1 >nul

echo [*] Starting Backend (port 8788)...
start "Kflower-Backend" cmd /c "cd /d D:\kkflower\kflower-backend && venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8788"
echo [*] Waiting for backend to start...
timeout /t 3 >nul

echo [*] Starting Frontend (port 5173)...
start "Kflower-Frontend" cmd /c "cd /d D:\kkflower\kflower-frontend && npm run dev"
echo [*] Waiting for frontend to start...
timeout /t 4 >nul

echo.
echo ========================================
echo   Checking services...
echo ========================================
netstat -ano | findstr ":8788 .*LISTENING" >nul
if %errorlevel%==0 (
    echo [OK] Backend:  http://127.0.0.1:8788
) else (
    echo [FAIL] Backend failed to start
)
netstat -ano | findstr ":5173 .*LISTENING" >nul
if %errorlevel%==0 (
    echo [OK] Frontend: http://localhost:5173
) else (
    echo [FAIL] Frontend failed to start
)

echo.
echo ========================================
echo   Frontend: http://localhost:5173
echo   Login:    admin / admin123
echo ========================================
echo.
pause