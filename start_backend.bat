@echo off
chcp 65001 >nul
cd /d "D:\kkflower\kflower-backend"
title Kflower 后端服务

echo ========================================
echo   Kflower 企业智能管理低代码平台
echo   后端服务启动脚本
echo ========================================
echo.

REM 检查虚拟环境
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] 虚拟环境已激活
) else (
    echo [INFO] 未找到虚拟环境，使用系统Python
)

REM 确保数据目录存在
if not exist "..\kflower-data" mkdir "..\kflower-data"
if not exist "..\kflower-data\uploads" mkdir "..\kflower-data\uploads"

echo.
echo [INFO] 启动后端服务...
echo [INFO] 访问地址: http://localhost:8788
echo [INFO] API文档: http://localhost:8788/docs
echo.

uvicorn main:app --host 0.0.0.0 --port 8788 --reload