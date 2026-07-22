@echo off
chcp 65001 >nul
cd /d "D:\kkflower\kflower-frontend"
title Kflower 前端服务

echo ========================================
echo   Kflower 企业智能管理低代码平台
echo   前端服务启动脚本
echo ========================================
echo.
echo [INFO] 启动前端开发服务器...
echo [INFO] 访问地址: http://localhost:5173
echo.

npm run dev