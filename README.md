# Kflower 企业智能管理低代码平台

基于 AI 大模型与多智能体系统的企业级低代码开发平台。

## 项目结构

```
kkflower/
├── kflower-backend/     # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/        # API路由
│   │   ├── core/       # 核心模块
│   │   │   ├── ai_digital_base/  # AI数字底座
│   │   │   └── agent_engine/     # 智能体引擎
│   │   ├── models/     # 数据库模型
│   │   ├── schemas/    # Pydantic模型
│   │   └── services/   # 业务服务
│   ├── main.py         # 应用入口
│   └── requirements.txt
│
├── kflower-frontend/    # 前端服务 (Vue3)
│   ├── src/
│   │   ├── app/        # 移动端
│   │   ├── common/     # 公共组件
│   │   └── pc/         # PC端
│   ├── dist/           # 构建输出
│   └── package.json
│
├── kflower-data/        # 数据目录（自动创建）
│   ├── kflower.db      # SQLite数据库
│   └── uploads/        # 文件上传目录
│
└── start_all.bat       # 一键启动脚本
```

## 快速启动

### 方式一：一键启动（推荐）

双击运行 `start_all.bat`，将同时启动：
- 后端服务：http://localhost:8898
- 前端服务：http://localhost:5111

### 方式二：分别启动

**后端：**
```bash
cd kflower-backend
python -m uvicorn main:app --host 0.0.0.0 --port 8898 --reload
```

**前端：**
```bash
cd kflower-frontend
npm run dev
```

## 默认账户

- 用户名：`admin`
- 密码：`admin123`

## 功能模块

### 1. AI智能对话
- 通用对话
- 模板设计助手
- 工作流设计助手
- 数据分析助手

### 2. 模板设计
- 可视化表单设计
- AI智能字段推荐
- 多模块组合
- 数据提交与管理

### 3. 流程审批
- 可视化流程设计
- 审批节点配置
- 流程执行追踪

### 4. 决策分析
- 数据可视化图表
- 智能问答分析
- 预测性洞察

### 5. 知识库RAG
- 文档上传解析
- 向量语义检索
- 检索增强生成

### 6. 系统管理
- 用户权限管理
- 组织架构管理
- 系统配置

## AI模型配置

系统支持多种AI提供商：

| 提供商 | 配置 |
|--------|------|
| SiliconFlow | API Key |
| DeepSeek | API Key + Base URL |
| 通义千问 | API Key |
| Ollama | 本地部署 |

配置方式：
1. 访问系统设置
2. 选择AI提供商
3. 填写API Key
4. 保存配置

## 技术栈

### 后端
- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- Pydantic
- LangChain/LangGraph
- Jieba分词

### 前端
- Vue 3 + TypeScript
- Element Plus
- Pinia (状态管理)
- Vue Router
- ECharts
- Vite

## API文档

启动服务后访问：http://localhost:8898/docs

## 注意事项

1. **首次启动**：数据目录和数据库会自动创建
2. **端口占用**：确保8898和5111端口未被占用
3. **AI功能**：需要配置有效的AI API Key才能使用AI功能
4. **文件上传**：上传目录会自动创建，无需手动配置

## 许可证

Private - All Rights Reserved
