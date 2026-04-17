@echo off
chcp 65001 >nul
title Kflower 完整服务

echo ========================================
echo   Kflower 企业智能管理低代码平台
echo   启动全部服务
echo ========================================
echo.

REM 启动后端
echo [INFO] 启动后端服务...
start "Kflower Backend" cmd /k "cd /d %~dp0kflower-backend && python -m uvicorn main:app --host 0.0.0.0 --port 8898 --reload"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
echo [INFO] 启动前端服务...
start "Kflower Frontend" cmd /k "cd /d %~dp0kflower-frontend && npm run dev"

echo.
echo ========================================
echo   服务已启动！
echo   后端: http://localhost:8898
echo   API文档: http://localhost:8898/docs
echo   前端: http://localhost:5111
echo ========================================
echo.
echo 按任意键退出此窗口（服务将继续运行）...
pause >nul
