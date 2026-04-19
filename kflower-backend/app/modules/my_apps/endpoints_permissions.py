"""
权限管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.workflow import Template
from app.modules.my_apps.models import Application, AppMenu
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/permissions", tags=["权限管理"])


# ============ 权限配置 ============
@router.get("/app/{app_id}", response_model=BaseResponse)
async def get_app_permissions(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用的完整权限配置"""
    # 获取应用
    app_result = await db.execute(select(Application).where(Application.id == app_id))
    app = app_result.scalar_one_or_none()
    if not app:
        return BaseResponse(success=False, message="应用不存在")

    # 获取所有角色
    roles_result = await db.execute(select(Role).where(Role.is_active == True))
    roles = roles_result.scalars().all()

    # 获取菜单
    menus_result = await db.execute(select(AppMenu).where(AppMenu.app_id == app_id))
    menus = menus_result.scalars().all()

    # 获取模板信息
    template_ids = [m.template_id for m in menus if m.template_id]
    templates_info = {}
    if template_ids:
        tpl_result = await db.execute(
            select(Template).where(Template.id.in_(template_ids))
        )
        for tpl in tpl_result.scalars().all():
            fields = []
            if tpl.modules:
                for mod in tpl.modules:
                    if isinstance(mod, dict) and 'fields' in mod:
                        fields.extend(mod['fields'])
            templates_info[tpl.id] = {
                "name": tpl.name,
                "fields": fields
            }

    # 获取已保存的权限配置
    app_config = app.config or {}
    permissions = app_config.get("permissions", {})

    return BaseResponse(data={
        "app_id": app_id,
        "app_name": app.name,
        "roles": [{"id": r.id, "name": r.name, "code": r.code} for r in roles],
        "menus": [
            {
                "id": m.id,
                "label": m.menu_label,
                "template_id": m.template_id,
                "icon": m.menu_icon,
            }
            for m in menus
        ],
        "templates": templates_info,
        "permissions": permissions
    })


@router.put("/app/{app_id}", response_model=BaseResponse)
async def save_app_permissions(
    app_id: int,
    config: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存应用的权限配置"""
    app_result = await db.execute(select(Application).where(Application.id == app_id))
    app = app_result.scalar_one_or_none()
    if not app:
        return BaseResponse(success=False, message="应用不存在")

    app_config = app.config or {}
    app_config["permissions"] = config
    app.config = app_config
    await db.commit()

    return BaseResponse(message="权限配置已保存")


# ============ 角色数据权限 ============
@router.get("/roles/{role_id}/data-permissions", response_model=BaseResponse)
async def get_role_data_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色的数据权限规则"""
    role_result = await db.execute(select(Role).where(Role.id == role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        return BaseResponse(success=False, message="角色不存在")

    rules = role.data_permission_rules or []
    return BaseResponse(data=rules)


@router.put("/roles/{role_id}/data-permissions", response_model=BaseResponse)
async def save_role_data_permissions(
    role_id: int,
    rules: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存角色的数据权限规则"""
    role_result = await db.execute(select(Role).where(Role.id == role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        return BaseResponse(success=False, message="角色不存在")

    role.data_permission_rules = rules
    await db.commit()

    return BaseResponse(message="数据权限规则已保存")


# ============ 审计日志 ============
@router.get("/audit-logs", response_model=BaseResponse)
async def get_audit_logs(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询审计日志"""
    from app.models.ai import AuditLog

    query = select(AuditLog)

    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == str(resource_id))
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    # 统计总数
    count_query = select(func.count()).select_from(AuditLog)
    if resource_type:
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    if user_id:
        count_query = count_query.where(AuditLog.user_id == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    # 获取操作用户信息
    user_ids = list(set(log.user_id for log in logs if log.user_id))
    users_info = {}
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        for user in user_result.scalars().all():
            users_info[user.id] = {"name": user.name, "username": user.username}

    return BaseResponse(data={
        "total": total,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": users_info.get(log.user_id, {}).get("name", "未知"),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    })


@router.get("/audit-logs/export", response_model=BaseResponse)
async def export_audit_logs(
    resource_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出审计日志为CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    from app.models.ai import AuditLog

    query = select(AuditLog)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    query = query.order_by(AuditLog.created_at.desc()).limit(1000)
    result = await db.execute(query)
    logs = result.scalars().all()

    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel
    writer = csv.writer(output)
    writer.writerow(["ID", "用户", "操作", "资源类型", "资源ID", "详情", "IP地址", "时间"])

    for log in logs:
        writer.writerow([
            log.id,
            log.user_id or "",
            log.action or "",
            log.resource_type or "",
            log.resource_id or "",
            str(log.detail) if log.detail else "",
            log.ip_address or "",
            log.created_at.isoformat() if log.created_at else ""
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue().encode('utf-8-sig')]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )
