@echo off
chcp 65001 >nul
title Kflower Stop

echo.
echo ========================================
echo   Kflower - Stopping Services...
echo ========================================
echo.

set STOPPED=0

:: Kill backend (port 8898)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8898 .*LISTENING"') do (
    echo [*] Stopping Backend (PID %%a)...
    taskkill /F /PID %%a 2>nul
    set STOPPED=1
)

:: Kill frontend dev server (port 5111)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5111 .*LISTENING"') do (
    echo [*] Stopping Frontend (PID %%a)...
    taskkill /F /PID %%a 2>nul
    set STOPPED=1
)

:: Also kill by window title
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Kflower-Frontend*" 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Kflower-Backend*" 2>nul

:: Kill any stray node processes in the kflower directories
for /f "tokens=2" %%a in ('wmic process where "name='node.exe'" get processid 2^|more +1') do (
    taskkill /F /PID %%a 2>nul
)

timeout /t 1 >nul

:: Verify
netstat -ano | findstr ":8898 .*LISTENING" >nul
if %errorlevel% neq 0 (
    echo [OK] Backend stopped
) else (
    echo [WARN] Backend still running
)

netstat -ano | findstr ":5111 .*LISTENING" >nul
if %errorlevel% neq 0 (
    echo [OK] Frontend stopped
) else (
    echo [WARN] Frontend still running
)

echo.
echo ========================================
echo   All services stopped!
echo ========================================
echo.
pause
