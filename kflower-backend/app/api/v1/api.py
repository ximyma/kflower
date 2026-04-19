"""
API v1 路由汇总
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, ai, templates, workflows, analytics, knowledge, dashboard, system, organizations, users, permissions, agent, import_, local_ai
from app.api.v1 import migration
from app.modules.my_apps import router as apps_router

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(ai.router)
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
api_router.include_router(apps_router)  # 我的应用模块
