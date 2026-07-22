"""
Generate all Kflower .bat files with consistent ports and paths.
Standard: Backend 8788, Frontend 5173
"""
import os

BASE = r"D:\kkflower"
BACKEND = os.path.join(BASE, "kflower-backend")
FRONTEND = os.path.join(BASE, "kflower-frontend")
VENV_PYTHON = r"venv\Scripts\python.exe"
BACKEND_PORT = "8788"
FRONTEND_PORT = "5173"

def write_bat(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines))

# ===== 1. start_all.bat =====
write_bat(os.path.join(BASE, "start_all.bat"), [
    "@echo off",
    "chcp 65001 >nul",
    "title Kflower 完整服务",
    "",
    "echo ========================================",
    "echo   Kflower 企业智能管理低代码平台",
    "echo   启动全部服务",
    "echo ========================================",
    "echo.",
    "",
    "REM 启动后端（使用虚拟环境）",
    "echo [INFO] 启动后端服务...",
    f'start "Kflower Backend" cmd /k "cd /d {BACKEND} && {VENV_PYTHON} -m uvicorn main:app --host 0.0.0.0 --port {BACKEND_PORT} --reload"',
    "",
    "REM 等待后端启动",
    "timeout /t 3 /nobreak >nul",
    "",
    "REM 启动前端",
    "echo [INFO] 启动前端服务...",
    f'start "Kflower Frontend" cmd /k "cd /d {FRONTEND} && npm run dev"',
    "",
    "echo.",
    "echo ========================================",
    f"echo   后端: http://localhost:{BACKEND_PORT}",
    f"echo   API文档: http://localhost:{BACKEND_PORT}/docs",
    f"echo   前端: http://localhost:{FRONTEND_PORT}",
    "echo ========================================",
    "echo.",
    "echo 按任意键退出此窗口（服务将继续运行）...",
    "pause >nul",
])

# ===== 2. start.bat (with cleanup) =====
write_bat(os.path.join(BASE, "start.bat"), [
    "@echo off",
    "chcp 65001 >nul",
    "title Kflower Startup",
    "",
    "echo.",
    "echo ========================================",
    "echo   Kflower - Starting Services...",
    "echo ========================================",
    "echo.",
    "",
    "REM Kill existing services",
    "echo [*] Stopping existing services...",
    f'for /f "tokens=5" %%a in (\'netstat -ano ^| findstr ":{BACKEND_PORT} " ^| findstr "LISTENING"\') do taskkill /F /PID %%a 2>nul',
    f'for /f "tokens=5" %%a in (\'netstat -ano ^| findstr ":{FRONTEND_PORT} " ^| findstr "LISTENING"\') do taskkill /F /PID %%a 2>nul',
    "timeout /t 1 >nul",
    "",
    f"echo [*] Starting Backend (port {BACKEND_PORT})...",
    f'start "Kflower-Backend" cmd /c "cd /d {BACKEND} && {VENV_PYTHON} -m uvicorn main:app --host 0.0.0.0 --port {BACKEND_PORT}"',
    "echo [*] Waiting for backend to start...",
    "timeout /t 3 >nul",
    "",
    f"echo [*] Starting Frontend (port {FRONTEND_PORT})...",
    f'start "Kflower-Frontend" cmd /c "cd /d {FRONTEND} && npm run dev"',
    "echo [*] Waiting for frontend to start...",
    "timeout /t 4 >nul",
    "",
    "echo.",
    "echo ========================================",
    "echo   Checking services...",
    "echo ========================================",
    f'netstat -ano | findstr ":{BACKEND_PORT} .*LISTENING" >nul',
    "if %errorlevel%==0 (",
    f"    echo [OK] Backend:  http://127.0.0.1:{BACKEND_PORT}",
    ") else (",
    "    echo [FAIL] Backend failed to start",
    ")",
    f'netstat -ano | findstr ":{FRONTEND_PORT} .*LISTENING" >nul',
    "if %errorlevel%==0 (",
    f"    echo [OK] Frontend: http://localhost:{FRONTEND_PORT}",
    ") else (",
    "    echo [FAIL] Frontend failed to start",
    ")",
    "",
    "echo.",
    "echo ========================================",
    f"echo   Frontend: http://localhost:{FRONTEND_PORT}",
    "echo   Login:    admin / admin123",
    "echo ========================================",
    "echo.",
    "pause",
])

# ===== 3. start_backend.bat =====
write_bat(os.path.join(BASE, "start_backend.bat"), [
    "@echo off",
    "chcp 65001 >nul",
    f'cd /d "{BACKEND}"',
    "title Kflower 后端服务",
    "",
    "echo ========================================",
    "echo   Kflower 企业智能管理低代码平台",
    "echo   后端服务启动脚本",
    "echo ========================================",
    "echo.",
    "",
    "REM 检查虚拟环境",
    "if exist venv\\Scripts\\activate.bat (",
    "    call venv\\Scripts\\activate.bat",
    "    echo [OK] 虚拟环境已激活",
    ") else (",
    "    echo [INFO] 未找到虚拟环境，使用系统Python",
    ")",
    "",
    "REM 确保数据目录存在",
    'if not exist "..\\kflower-data" mkdir "..\\kflower-data"',
    'if not exist "..\\kflower-data\\uploads" mkdir "..\\kflower-data\\uploads"',
    "",
    "echo.",
    "echo [INFO] 启动后端服务...",
    f"echo [INFO] 访问地址: http://localhost:{BACKEND_PORT}",
    f"echo [INFO] API文档: http://localhost:{BACKEND_PORT}/docs",
    "echo.",
    "",
    f"uvicorn main:app --host 0.0.0.0 --port {BACKEND_PORT} --reload",
])

# ===== 4. start_frontend.bat =====
write_bat(os.path.join(BASE, "start_frontend.bat"), [
    "@echo off",
    "chcp 65001 >nul",
    f'cd /d "{FRONTEND}"',
    "title Kflower 前端服务",
    "",
    "echo ========================================",
    "echo   Kflower 企业智能管理低代码平台",
    "echo   前端服务启动脚本",
    "echo ========================================",
    "echo.",
    "echo [INFO] 启动前端开发服务器...",
    f"echo [INFO] 访问地址: http://localhost:{FRONTEND_PORT}",
    "echo.",
    "",
    "npm run dev",
])

# ===== 5. kflower-backend/启动.bat =====
write_bat(os.path.join(BACKEND, "启动.bat"), [
    "@echo off",
    "chcp 65001 >nul",
    "title Kflower 后端服务",
    "",
    "echo ========================================",
    "echo   Kflower 企业智能管理低代码平台",
    "echo   后端服务启动脚本",
    "echo ========================================",
    "echo.",
    "",
    "cd /d \"%~dp0\"",
    "",
    "REM 激活虚拟环境",
    "if exist venv\\Scripts\\activate.bat (",
    "    call venv\\Scripts\\activate.bat",
    "    echo [OK] 虚拟环境已激活",
    ") else (",
    "    echo [WARNING] 未找到虚拟环境，正在创建...",
    "    python -m venv venv",
    "    call venv\\Scripts\\activate.bat",
    "    echo [INFO] 安装依赖包...",
    "    pip install -r requirements.txt",
    ")",
    "",
    "echo.",
    "echo [INFO] 启动后端服务...",
    f"echo [INFO] 访问地址: http://localhost:{BACKEND_PORT}",
    f"echo [INFO] API文档: http://localhost:{BACKEND_PORT}/docs",
    "echo.",
    "",
    f"uvicorn main:app --host 0.0.0.0 --port {BACKEND_PORT} --reload",
])

print("All bat files generated successfully!")
print(f"  Backend port:  {BACKEND_PORT}")
print(f"  Frontend port: {FRONTEND_PORT}")
print(f"  Python:        {VENV_PYTHON}")
print(f"  Entry point:   main:app")
