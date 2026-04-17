"""
业务服务 - 移动端设置服务
跨端适配引擎
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json


class MobileService:
    """移动端设置服务 - 跨端适配"""
    
    # 移动端主题
    MOBILE_THEMES = {
        "light": {
            "name": "浅色主题",
            "colors": {
                "primary": "#409EFF",
                "background": "#F5F7FA",
                "card": "#FFFFFF",
                "text": "#303133"
            }
        },
        "dark": {
            "name": "深色主题",
            "colors": {
                "primary": "#409EFF",
                "background": "#1A1A1A",
                "card": "#2D2D2D",
                "text": "#E6E6E6"
            }
        },
        "auto": {
            "name": "跟随系统",
            "colors": {}
        }
    }
    
    # 移动端功能开关
    FEATURE_FLAGS = {
        "ai_chat": {"name": "AI对话", "default": True, "description": "启用AI智能助手"},
        "quick_actions": {"name": "快捷操作", "default": True, "description": "首页快捷操作"},
        "offline_mode": {"name": "离线模式", "default": False, "description": "支持离线访问"},
        "push_notifications": {"name": "推送通知", "default": True, "description": "接收系统通知"},
        "biometric": {"name": "生物识别", "default": False, "description": "指纹/面容登录"}
    }
    
    @classmethod
    async def get_mobile_config(
        cls,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """获取移动端配置"""
        from app.models.ai import SystemConfig
        
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.key == f"mobile_config_{user_id}"
            )
        )
        config = result.scalar_one_or_none()
        
        if config and config.value:
            try:
                return json.loads(config.value)
            except:
                pass
        
        # 返回默认配置
        return cls._default_mobile_config()
    
    @classmethod
    async def save_mobile_config(
        cls,
        user_id: int,
        config: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """保存移动端配置"""
        from app.models.ai import SystemConfig
        
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.key == f"mobile_config_{user_id}"
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.value = json.dumps(config)
        else:
            config_record = SystemConfig(
                key=f"mobile_config_{user_id}",
                value=json.dumps(config),
                description="移动端配置",
                organization_id=None
            )
            db.add(config_record)
        
        await db.commit()
        return True
    
    @classmethod
    async def update_theme(
        cls,
        user_id: int,
        theme: str,
        db: AsyncSession
    ) -> bool:
        """更新主题"""
        config = await cls.get_mobile_config(user_id, db)
        config["theme"] = theme
        return await cls.save_mobile_config(user_id, config, db)
    
    @classmethod
    async def update_features(
        cls,
        user_id: int,
        features: Dict[str, bool],
        db: AsyncSession
    ) -> bool:
        """更新功能开关"""
        config = await cls.get_mobile_config(user_id, db)
        config["features"] = features
        return await cls.save_mobile_config(user_id, config, db)
    
    @classmethod
    async def get_themes(cls) -> List[Dict[str, Any]]:
        """获取可用主题"""
        return [
            {"key": key, "name": theme["name"], "colors": theme["colors"]}
            for key, theme in cls.MOBILE_THEMES.items()
        ]
    
    @classmethod
    async def get_feature_flags(cls) -> List[Dict[str, Any]]:
        """获取功能开关列表"""
        return [
            {"key": key, **flag}
            for key, flag in cls.FEATURE_FLAGS.items()
        ]
    
    @classmethod
    def _default_mobile_config(cls) -> Dict[str, Any]:
        """默认移动端配置"""
        return {
            "theme": "light",
            "features": {k: v["default"] for k, v in cls.FEATURE_FLAGS.items()},
            "tabbar": ["home", "work", "profile"],
            "shortcuts": [
                {"name": "新建", "icon": "plus", "action": "create"},
                {"name": "扫描", "icon": "scan", "action": "scan"},
                {"name": "AI助手", "icon": "ai", "action": "ai"}
            ]
        }


mobile_service = MobileService()
