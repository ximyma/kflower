@echo off
chcp 65001 >nul
title Kflower 完整服务

echo ========================================
echo   Kflower 企业智能管理低代码平台
echo   启动全部服务
echo ========================================
echo.

REM 启动后端（使用虚拟环境）
echo [INFO] 启动后端服务...
start "Kflower Backend" cmd /k "cd /d D:\kkflower\kflower-backend && venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8788 --reload"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
echo [INFO] 启动前端服务...
start "Kflower Frontend" cmd /k "cd /d D:\kkflower\kflower-frontend && npm run dev"

echo.
echo ========================================
echo   后端: http://localhost:8788
echo   API文档: http://localhost:8788/docs
echo   前端: http://localhost:5173
echo ========================================
echo.
echo 按任意键退出此窗口（服务将继续运行）...
pause >nul