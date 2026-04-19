"""
我的应用模块
"""
from app.modules.my_apps.models import Application, AppMenu, FormRelation, AppPlugin
from app.modules.my_apps.endpoints import router
from app.modules.my_apps.service import my_apps_service

__all__ = [
    "Application",
    "AppMenu", 
    "FormRelation",
    "AppPlugin",
    "router",
    "my_apps_service"
]
