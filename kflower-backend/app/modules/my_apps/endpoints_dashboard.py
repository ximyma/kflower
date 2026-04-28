"""
仪表盘管理 API
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.modules.my_apps.models import Application
from app.modules.my_apps.analytics_engine import analytics_engine
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/apps", tags=["仪表盘管理"])


def _parse_config(raw: Any) -> dict:
    """兼容 aiosqlite 下 JSON 字段为字符串的情况"""
    if isinstance(raw, str):
        return json.loads(raw) if raw else {}
    return raw or {}


@router.get("/{app_id}/dashboard", response_model=BaseResponse)
async def get_dashboard_config(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用的仪表盘配置"""
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        return BaseResponse(success=False, message="应用不存在")

    config = _parse_config(app.config)
    dashboard_config = config.get("dashboard", {"pages": [{"name": "首页", "widgets": []}]})

    return BaseResponse(data=dashboard_config)


@router.put("/{app_id}/dashboard", response_model=BaseResponse)
async def save_dashboard_config(
    app_id: int,
    config: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存应用的仪表盘配置"""
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        return BaseResponse(success=False, message="应用不存在")

    app_config = _parse_config(app.config)
    app_config["dashboard"] = config
    app.config = app_config
    # aiosqlite 下 JSON 列直接赋值不会触发 SA 脏检测，必须显式标记
    flag_modified(app, "config")
    await db.commit()

    return BaseResponse(message="仪表盘配置已保存")


@router.post("/dashboard/widget/data", response_model=BaseResponse)
async def get_widget_data(
    widget_config: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘组件的数据（实时刷新）"""
    try:
        # 兼容两种请求格式：
        # 1. 直接发送 data_source 对象
        # 2. 发送完整 widget 对象，data_source 在内部
        data_source = widget_config.get("data_source") or widget_config

        if not data_source:
            return BaseResponse(success=False, message="未配置数据源")

        # 如果 data_source 是字符串，尝试解析
        if isinstance(data_source, str):
            try:
                data_source = json.loads(data_source)
            except:
                return BaseResponse(success=False, message="数据源格式不正确（JSON字符串解析失败）")

        if not isinstance(data_source, dict):
            return BaseResponse(success=False, message=f"数据源格式不正确（期望dict，实际{type(data_source).__name__}）")

        # 兼容 aiosqlite 下 JSON 字符串字段
        if isinstance(data_source.get("filters"), str):
            try:
                data_source["filters"] = json.loads(data_source["filters"])
            except:
                data_source["filters"] = []

        result = await analytics_engine.execute_aggregation(db, data_source, current_user.id)

        if "error" in result:
            return BaseResponse(success=False, message=result["error"])

        # 把列名替换为中文标签
        template_id = data_source.get("template_id")
        if template_id and result.get("data"):
            try:
                from app.modules.my_apps.analytics_engine import AnalyticsEngine
                fields_result = await db.execute(
                    text("SELECT modules FROM templates WHERE id = :tid"),
                    {"tid": template_id}
                )
                fields_row = fields_result.fetchone()
                if fields_row:
                    modules = AnalyticsEngine._parse_config(fields_row[0])
                    field_labels = {}
                    for mod in (modules if isinstance(modules, list) else []):
                        for f in mod.get("fields", []):
                            fname = f.get("name", "")
                            if fname:
                                field_labels[fname] = f.get("label", fname)
                    if field_labels:
                        for row in result["data"]:
                            for k in list(row.keys()):
                                if k in field_labels:
                                    new_key = field_labels[k]
                                    if new_key != k:
                                        row[new_key] = row.pop(k)
            except Exception:
                pass

        return BaseResponse(data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.get("/dashboard/templates", response_model=BaseResponse)
async def get_dashboard_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可用于仪表盘的模板列表"""
    from app.models.workflow import Template

    result = await db.execute(
        select(Template).where(
            Template.is_published == True,
            Template.is_deleted == False
        ).order_by(Template.updated_at.desc()).limit(50)
    )
    templates = result.scalars().all()

    return BaseResponse(data=[
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
        }
        for t in templates
    ])
