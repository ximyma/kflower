"""
业务服务 - 工作台设置服务
个性化配置引擎
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json


class WorkbenchService:
    """工作台设置服务 - 个性化配置"""
    
    # 预设工作台模板
    WORKBENCH_TEMPLATES = {
        "default": {
            "name": "默认工作台",
            "description": "标准功能工作台",
            "widgets": [
                {"id": "welcome", "type": "banner", "title": "欢迎", "config": {}},
                {"id": "kpi", "type": "kpi", "title": "关键指标", "config": {"metrics": ["销售额", "订单数"]}},
                {"id": "todo", "type": "list", "title": "待办事项", "config": {"max_items": 5}},
                {"id": "recent", "type": "list", "title": "最近操作", "config": {"max_items": 5}},
                {"id": "quick", "type": "shortcuts", "title": "快捷操作", "config": {}}
            ]
        },
        "manager": {
            "name": "经理工作台",
            "description": "管理者专用视图",
            "widgets": [
                {"id": "welcome", "type": "banner", "title": "欢迎", "config": {}},
                {"id": "kpi", "type": "kpi", "title": "关键指标", "config": {"metrics": ["销售额", "订单数", "客户增长"]}},
                {"id": "approval", "type": "list", "title": "待审批", "config": {"max_items": 8}},
                {"id": "chart", "type": "chart", "title": "数据趋势", "config": {"type": "line"}},
                {"id": "notice", "type": "notice", "title": "公告", "config": {}}
            ]
        },
        "sales": {
            "name": "销售工作台",
            "description": "销售团队专用",
            "widgets": [
                {"id": "welcome", "type": "banner", "title": "欢迎", "config": {}},
                {"id": "kpi", "type": "kpi", "title": "销售指标", "config": {"metrics": ["销售额", "新客户", "跟进中"]}},
                {"id": "tasks", "type": "list", "title": "今日任务", "config": {}},
                {"id": "customers", "type": "list", "title": "重点客户", "config": {"limit": 5}},
                {"id": "rank", "type": "rank", "title": "业绩排行", "config": {}}
            ]
        }
    }
    
    @classmethod
    async def get_workbench_config(
        cls,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """获取工作台配置"""
        from app.models.ai import SystemConfig
        
        # 查询用户个性化配置
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.key == f"workbench_config_{user_id}"
            )
        )
        config = result.scalar_one_or_none()
        
        if config and config.value:
            try:
                return json.loads(config.value)
            except:
                pass
        
        # 返回默认配置
        return cls.WORKBENCH_TEMPLATES["default"]
    
    @classmethod
    async def save_workbench_config(
        cls,
        user_id: int,
        config: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """保存工作台配置"""
        from app.models.ai import SystemConfig
        
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.key == f"workbench_config_{user_id}"
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.value = json.dumps(config)
        else:
            config_record = SystemConfig(
                key=f"workbench_config_{user_id}",
                value=json.dumps(config),
                description="用户工作台配置",
                organization_id=None
            )
            db.add(config_record)
        
        await db.commit()
        return True
    
    @classmethod
    async def get_templates(cls) -> List[Dict[str, Any]]:
        """获取工作台模板"""
        return [
            {
                "key": key,
                "name": template["name"],
                "description": template["description"],
                "widget_count": len(template["widgets"])
            }
            for key, template in cls.WORKBENCH_TEMPLATES.items()
        ]
    
    @classmethod
    async def reset_workbench(
        cls,
        user_id: int,
        template_key: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """重置工作台"""
        template = cls.WORKBENCH_TEMPLATES.get(template_key, cls.WORKBENCH_TEMPLATES["default"])
        
        config = {
            "template": template_key,
            "widgets": template["widgets"]
        }
        
        await cls.save_workbench_config(user_id, config, db)
        
        return config


workbench_service = WorkbenchService()
