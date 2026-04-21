"""
API v1 路由汇总
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, ai, templates, workflows, analytics, knowledge, dashboard, system, organizations, users, permissions, agent, import_, local_ai, ai_capability, ai_digital_base, ai_agent_engine, doc_converter, notifications
from app.api.v1 import migration
from app.modules.my_apps import router as apps_router

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(ai.router)
api_router.include_router(ai_capability.router)
api_router.include_router(ai_digital_base.router)
api_router.include_router(ai_agent_engine.router)
api_router.include_router(templates.router)
api_router.include_router(workflows.router)
api_router.include_router(analytics.router)
api_router.include_router(knowledge.router)
api_router.include_router(migration.router)
api_router.include_router(dashboard.router)
api_router.include_router(system.router)
api_router.include_router(organizations.router)
api_router.include_router(users.router)
api_router.include_router(permissions.router)
api_router.include_router(agent.router)
api_router.include_router(import_.router)
api_router.include_router(local_ai.router)
api_router.include_router(doc_converter.router)  # 文档转换工具
api_router.include_router(notifications.router)  # 通知发送工具
api_router.include_router(apps_router)  # 我的应用模块

# 我的应用模块扩展路由
from app.modules.my_apps import endpoints_plugins
from app.modules.my_apps import endpoints_dashboard
from app.modules.my_apps import endpoints_permissions

api_router.include_router(endpoints_plugins.router)  # 插件管理
api_router.include_router(endpoints_dashboard.router)  # 仪表盘
api_router.include_router(endpoints_permissions.router)  # 权限管理
