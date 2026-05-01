# KFlower v1.0 里程碑版 - 打包部署方案

> **版本**: 1.0.0  
> **日期**: 2026年5月1日  
> **目标**: 将 KFlower 智能低代码平台打包为可部署的生产版本

---

## 📋 目录

1. [部署架构概述](#1-部署架构概述)
2. [环境准备](#2-环境准备)
3. [后端部署](#3-后端部署)
4. [前端部署](#4-前端部署)
5. [数据库配置](#5-数据库配置)
6. [AI 服务配置](#6-ai-服务配置)
7. [反向代理配置](#7-反向代理配置)
8. [SSL 证书配置](#8-ssl-证书配置)
9. [Docker 部署方案](#9-docker-部署方案)
10. [生产环境检查清单](#10-生产环境检查清单)
11. [备份与恢复](#11-备份与恢复)
12. [监控与日志](#12-监控与日志)
13. [常见问题排查](#13-常见问题排查)

---

## 1. 部署架构概述

### 1.1 单机部署架构

```
                        ┌─────────────────┐
                        │   用户浏览器     │
                        └────────┬────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Nginx 反向代理                           │
│                    (端口 80/443, SSL Termination)                │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
              ┌─────────────────┴─────────────────┐
              │                                       │
              ▼                                       ▼
┌─────────────────────────┐             ┌─────────────────────────┐
│    前端服务              │             │    后端 API 服务        │
│    (Vite/Node)           │             │    (FastAPI/uvicorn)   │
│    端口: 5173            │             │    端口: 8000          │
│    /usr/share/kflower/   │             │    /opt/kflower/backend│
└─────────────────────────┘             └───────────┬─────────────┘
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              │                       │                       │
                              ▼                       ▼                       ▼
                    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
                    │   SQLite DB     │   │   文件存储       │   │   AI 服务       │
                    │   /data/        │   │   /uploads/     │   │   OpenAI API   │
                    └─────────────────┘   └─────────────────┘   └─────────────────┘
```

### 1.2 部署方式选择

| 部署方式 | 适用场景 | 复杂度 |
|----------|----------|--------|
| **Docker Compose** | 快速部署、演示环境 | ⭐ |
| **手动部署** | 生产环境、定制需求 | ⭐⭐⭐ |
| **K8s 部署** | 大规模集群 | ⭐⭐⭐⭐⭐ |

---

## 2. 环境准备

### 2.1 服务器要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 50 GB | 100 GB+ SSD |
| 系统 | CentOS 7+ / Ubuntu 20.04+ / Windows Server 2019+ | - |

### 2.2 安装基础软件

#### Linux (Ubuntu 20.04)

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git unzip nginx certbot python3 python3-pip

# 安装 Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version  # v18.x.x
npm --version   # 9.x.x
python3 --version  # 3.11.x
```

#### Windows Server 2019

```powershell
# 安装 Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装依赖
choco install -y nodejs git python311.putty

# 验证安装
node --version
npm --version
```

### 2.3 创建部署用户

```bash
# 创建专用用户（Linux）
sudo useradd -m -s /bin/bash kflower
sudo mkdir -p /opt/kflower
sudo chown -R kflower:kflower /opt/kflower
```

---

## 3. 后端部署

### 3.1 获取代码

```bash
# 克隆代码（如果使用 Git）
cd /opt/kflower
git clone https://your-repo/kflower.git kflower-backend

# 或解压发布包
unzip kflower-backend-v1.0.zip -d /opt/kflower/
```

### 3.2 创建虚拟环境

```bash
cd /opt/kflower/kflower-backend

# 创建 Python 虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 配置文件

创建 `config.yaml`：

```yaml
# 数据库配置
database:
  url: "sqlite:///./data/kflower.db"  # SQLite
  # url: "postgresql://user:password@localhost/kflower"  # PostgreSQL

# 文件上传
upload:
  path: "./uploads"
  max_size: 10485760  # 10MB

# JWT 配置
jwt:
  secret_key: "your-super-secret-key-change-in-production"
  algorithm: "HS256"
  access_token_expire_minutes: 1440  # 24小时

# CORS 配置
cors:
  allow_origins: ["http://localhost:5173", "http://your-domain.com"]
  allow_credentials: true

# AI 配置
ai:
  default_provider: "openai"
  api_key: "your-openai-api-key"
  base_url: "https://api.openai.com/v1"

# 应用配置
app:
  title: "KFlower 智能低代码平台"
  version: "1.0.0"
  debug: false  # 生产环境必须为 false
```

### 3.4 初始化数据库

```bash
# 创建数据目录
mkdir -p /opt/kflower/kflower-backend/data
mkdir -p /opt/kflower/kflower-backend/uploads

# 初始化数据库（首次运行自动创建）
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 3.5 启动后端服务

#### 开发环境启动

```bash
cd /opt/kflower/kflower-backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 生产环境启动

使用 systemd 服务：

```bash
# 创建服务文件
sudo tee /etc/systemd/system/kflower-backend.service > /dev/null <<EOF
[Unit]
Description=KFlower Backend API Service
After=network.target

[Service]
User=kflower
Group=kflower
WorkingDirectory=/opt/kflower/kflower-backend
Environment="PATH=/opt/kflower/kflower-backend/venv/bin"
ExecStart=/opt/kflower/kflower-backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable kflower-backend
sudo systemctl start kflower-backend

# 检查状态
sudo systemctl status kflower-backend
```

#### 使用 Gunicorn + Uvicorn Workers

```bash
# 安装 gunicorn
pip install gunicorn

# 启动（4个 worker）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
```

### 3.6 验证后端服务

```bash
# 测试 API
curl http://localhost:8000/api/v1/health

# 应返回
{"status":"ok","message":"KFlower API is running"}
```

---

## 4. 前端部署

### 4.1 构建前端

```bash
cd /opt/kflower/kflower-frontend

# 安装依赖
npm install

# 配置 API 地址
# 编辑 .env.production
echo "VITE_API_BASE_URL=http://your-domain.com/api/v1" > .env.production

# 构建生产版本
npm run build
```

### 4.2 Nginx 配置

创建 Nginx 配置文件：

```bash
sudo tee /etc/nginx/sites-available/kflower > /dev/null <<'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    # 前端静态文件
    root /usr/share/kflower;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 上传文件大小限制
    client_max_body_size 50M;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/kflower /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl reload nginx
```

### 4.3 部署前端文件

```bash
# 复制构建文件
sudo rm -rf /usr/share/kflower
sudo mkdir -p /usr/share/kflower
sudo cp -r /opt/kflower/kflower-frontend/dist/* /usr/share/kflower/
sudo chown -R www-data:www-data /usr/share/kflower
```

### 4.4 Windows IIS 部署

1. 安装 IIS 并启用 ASP.NET Core 模块
2. 发布前端为静态文件
3. 配置 URL Rewrite：

```xml
<!-- web.config -->
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="SPA Fallback" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

---

## 5. 数据库配置

### 5.1 SQLite（轻量级/演示）

默认使用，无需额外配置：

```yaml
database:
  url: "sqlite:///./data/kflower.db"
```

### 5.2 PostgreSQL（生产环境推荐）

```bash
# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 创建数据库
sudo -u postgres psql
CREATE DATABASE kflower;
CREATE USER kflower_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE kflower TO kflower_user;
\q

# 配置 pg_hba.conf 允许连接
# 添加: host all all 127.0.0.1/32 md5
sudo systemctl restart postgresql
```

修改配置：

```yaml
database:
  url: "postgresql://kflower_user:your_password@localhost/kflower"
  pool_size: 10
  max_overflow: 20
```

### 5.3 数据库迁移

```bash
# 执行数据库迁移
cd /opt/kflower/kflower-backend
source venv/bin/activate

# 首次运行自动创建所有表
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# 或运行 Alembic 迁移
alembic upgrade head
```

---

## 6. AI 服务配置

### 6.1 OpenAI API

```yaml
ai:
  default_provider: "openai"
  api_key: "sk-xxxxx"
  base_url: "https://api.openai.com/v1"
  models:
    - gpt-4o
    - gpt-4o-mini
    - gpt-4-turbo
```

### 6.2 Azure OpenAI

```yaml
ai:
  default_provider: "azure"
  api_key: "your-azure-key"
  base_url: "https://your-resource.openai.azure.com"
  api_version: "2024-02-01"
  deployment_name: "gpt-4o"
```

### 6.3 本地模型（Ollama）

```yaml
ai:
  default_provider: "ollama"
  base_url: "http://localhost:11434"
  models:
    - llama3
    - qwen2.5
    - deepseek-r1
```

### 6.4 配置 AI 能力

在后端配置文件中启用 AI 能力：

```yaml
capabilities:
  text_generation: true
  conversation: true
  code_generation: true
  data_analysis: true
```

---

## 7. 反向代理配置

### 7.1 负载均衡（多后端实例）

```nginx
upstream kflower_backend {
    least_conn;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://kflower_backend/;
        # ... 其他 proxy_set_header 配置
    }
}
```

### 7.2 WebSocket 支持（AI 对话）

```nginx
location /api/v1/ai/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    # ... 其他配置
}
```

---

## 8. SSL 证书配置

### 8.1 Let's Encrypt 免费证书

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 8.2 自签名证书（测试环境）

```bash
# 生成私钥
openssl genrsa -out /etc/ssl/private/kflower.key 2048

# 生成证书
openssl req -new -x509 -key /etc/ssl/private/kflower.key -out /etc/ssl/certs/kflower.crt -days 365

# 配置 Nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/kflower.crt;
    ssl_certificate_key /etc/ssl/private/kflower.key;
    # ...
}
```

---

## 9. Docker 部署方案

### 9.1 Docker Compose 文件

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # 前端服务
  frontend:
    image: nginx:alpine
    container_name: kflower-frontend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
    networks:
      - kflower-net

  # 后端服务
  backend:
    image: python:3.11-slim
    container_name: kflower-backend
    working_dir: /app
    volumes:
      - ./backend:/app
      - ./data:/app/data
      - ./uploads:/app/uploads
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/kflower.db
      - JWT_SECRET_KEY=${JWT_SECRET}
      - AI_API_KEY=${AI_API_KEY}
    command: >
      sh -c "pip install -r requirements.txt &&
             uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4"
    networks:
      - kflower-net

  # PostgreSQL（可选）
  db:
    image: postgres:15-alpine
    container_name: kflower-db
    environment:
      - POSTGRES_DB=kflower
      - POSTGRES_USER=kflower
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - kflower-net

volumes:
  postgres_data:

networks:
  kflower-net:
    driver: bridge
```

### 9.2 Nginx 配置

创建 `nginx/nginx.conf`：

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 9.3 启动 Docker

```bash
# 设置环境变量
export JWT_SECRET="your-super-secret-key"
export AI_API_KEY="your-openai-key"
export DB_PASSWORD="your-db-password"

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 10. 生产环境检查清单

### 10.1 安全检查

- [ ] 修改默认管理员密码
- [ ] 使用强 JWT 密钥（32位以上随机字符串）
- [ ] 启用 HTTPS (SSL)
- [ ] 配置防火墙（只开放 80/443）
- [ ] 关闭 debug 模式
- [ ] 数据库配置访问密码

### 10.2 性能检查

- [ ] 启用 Gzip 压缩
- [ ] 配置静态资源缓存
- [ ] 数据库连接池配置
- [ ] 合理设置 worker 数量
- [ ] 启用 Nginx 缓存

### 10.3 可靠性检查

- [ ] 配置日志轮转
- [ ] 设置监控告警
- [ ] 配置数据备份
- [ ] 测试服务重启

---

## 11. 备份与恢复

### 11.1 自动备份脚本

创建 `backup.sh`：

```bash
#!/bin/bash
# KFlower 备份脚本

BACKUP_DIR="/opt/backups/kflower"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
echo "备份数据库..."
cp /opt/kflower/kflower-backend/data/kflower.db "$BACKUP_DIR/db_$DATE.db"

# 备份上传文件
echo "备份上传文件..."
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /opt/kflower/kflower-backend/uploads

# 备份配置文件
echo "备份配置文件..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/kflower/kflower-backend/config.yaml

# 清理旧备份
echo "清理过期备份..."
find $BACKUP_DIR -name "*.db" -mtime +$KEEP_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$KEEP_DAYS -delete

echo "备份完成: $DATE"
```

添加到 crontab：

```bash
# 每天凌晨 3 点执行备份
0 3 * * * /opt/scripts/backup.sh >> /var/log/kflower_backup.log 2>&1
```

### 11.2 恢复数据

```bash
# 停止服务
sudo systemctl stop kflower-backend

# 恢复数据库
cp /opt/backups/kflower/db_20260501_030000.db /opt/kflower/kflower-backend/data/kflower.db

# 恢复上传文件
tar -xzf /opt/backups/kflower/uploads_20260501_030000.tar.gz -C /

# 重启服务
sudo systemctl start kflower-backend
```

---

## 12. 监控与日志

### 12.1 日志配置

Python 日志配置 (`logging.conf`)：

```ini
[loggers]
keys=root,app

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=defaultFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_app]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=app
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=defaultFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=handlers.RotatingFileHandler
level=DEBUG
formatter=defaultFormatter
args=('/var/log/kflower/app.log', 'a', 10485760, 5)

[formatter_defaultFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 12.2 系统监控

使用 Prometheus + Grafana：

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 12.3 健康检查

添加健康检查端点：

```bash
# 检查后端
curl http://localhost:8000/health

# 检查数据库
sqlite3 /opt/kflower/kflower-backend/data/kflower.db "SELECT COUNT(*) FROM users;"

# 检查磁盘空间
df -h /opt/kflower
```

---

## 13. 常见问题排查

### 13.1 502 Bad Gateway

**原因**: Nginx 无法连接到后端

**排查**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查端口监听
netstat -tlnp | grep 8000

# 查看 Nginx 错误日志
tail -f /var/log/nginx/error.log
```

### 13.2 前端空白页面

**排查**:
```bash
# 检查构建文件是否存在
ls -la /usr/share/kflower/

# 检查静态资源权限
ls -la /usr/share/kflower/assets/

# 检查 Nginx 配置
nginx -t
```

### 13.3 数据库连接失败

**排查**:
```bash
# SQLite
ls -la /opt/kflower/kflower-backend/data/kflower.db

# PostgreSQL
sudo -u postgres psql -c "SELECT 1;"

# 检查连接字符串
cat /opt/kflower/kflower-backend/config.yaml
```

### 13.4 AI 功能不可用

**排查**:
```bash
# 检查 API Key 配置
grep -r "api_key" /opt/kflower/kflower-backend/config.yaml

# 测试 API 连接
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"test"}]}'

# 查看后端日志
tail -f /var/log/kflower/app.log | grep -i ai
```

### 13.5 文件上传失败

**排查**:
```bash
# 检查上传目录权限
ls -la /opt/kflower/kflower-backend/uploads/

# 检查磁盘空间
df -h

# 检查 Nginx 上传大小限制
grep client_max_body_size /etc/nginx/nginx.conf
```

---

## 📋 快速部署命令汇总

### Linux 单机一键部署

```bash
#!/bin/bash
set -e

# 1. 安装依赖
apt update && apt install -y python3-venv python3-pip nginx

# 2. 创建目录
mkdir -p /opt/kflower/{backend,frontend,data,uploads}

# 3. 部署后端
cd /opt/kflower/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 启动后端
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > /var/log/kflower-backend.log 2>&1 &

# 5. 构建前端
cd /opt/kflower/frontend
npm install
npm run build

# 6. 配置 Nginx
cp /opt/kflower/deploy/nginx.conf /etc/nginx/sites-available/kflower
ln -sf /etc/nginx/sites-available/kflower /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "部署完成！访问 http://your-server-ip"
```

---

## 🎯 部署验证

部署完成后，访问系统验证以下功能：

1. ✅ 登录页面正常显示
2. ✅ 管理员登录成功
3. ✅ 表单设计器加载正常
4. ✅ 新建模板保存成功
5. ✅ 我的应用创建成功
6. ✅ AI 对话功能正常（配置了 API Key）

---

*文档版本: 1.0.0 | 最后更新: 2026-05-01*
