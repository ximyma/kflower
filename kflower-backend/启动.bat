@echo off
chcp 65001 >nul
title Kflower 后端服务

echo ========================================
echo   Kflower 企业智能管理低代码平台
echo   后端服务启动脚本
echo ========================================
echo.

cd /d "%~dp0"

REM 激活虚拟环境
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] 虚拟环境已激活
) else (
    echo [WARNING] 未找到虚拟环境，正在创建...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [INFO] 安装依赖包...
    pip install -r requirements.txt
)

echo.
echo [INFO] 启动后端服务...
echo [INFO] 访问地址: http://localhost:8898
echo [INFO] API文档: http://localhost:8898/docs
echo.

REM 启动服务
python main.py
