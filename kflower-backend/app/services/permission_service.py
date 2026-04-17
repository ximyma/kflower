"""
业务服务 - 用户权限服务
智能安全引擎
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime
import json

from app.models.user import User, Role, UserRole, Organization
from app.core.security import get_password_hash, verify_password


class PermissionService:
    """用户权限服务 - 智能安全引擎"""
    
    # 系统内置角色
    SYSTEM_ROLES = {
        "superadmin": {
            "name": "超级管理员",
            "code": "superadmin",
            "description": "拥有系统所有权限",
            "is_system": True,
            "permissions": ["*"]
        },
        "admin": {
            "name": "系统管理员",
            "code": "admin",
            "description": "管理系统配置和用户",
            "is_system": True,
            "permissions": [
                "system:*", "user:*", "role:*", "organization:*",
                "template:*", "workflow:*", "analytics:*", "knowledge:*"
            ]
        },
        "manager": {
            "name": "部门经理",
            "code": "manager",
            "description": "管理部门成员和审批",
            "is_system": True,
            "permissions": [
                "template:read", "template:write",
                "workflow:*", "analytics:read",
                "knowledge:read", "knowledge:write"
            ]
        },
        "user": {
            "name": "普通用户",
            "code": "user",
            "description": "使用基础功能",
            "is_system": True,
            "permissions": [
                "template:read", "workflow:read", "workflow:execute",
                "analytics:read", "knowledge:read"
            ]
        },
        "guest": {
            "name": "访客",
            "code": "guest",
            "description": "只读权限",
            "is_system": True,
            "permissions": [
                "template:read", "knowledge:read"
            ]
        }
    }
    
    # 权限定义
    PERMISSIONS = {
        "system": ["view", "config"],
        "user": ["view", "create", "edit", "delete", "export"],
        "role": ["view", "create", "edit", "delete"],
        "organization": ["view", "create", "edit", "delete"],
        "template": ["view", "create", "edit", "delete", "publish"],
        "workflow": ["view", "create", "edit", "delete", "execute", "approve"],
        "analytics": ["view", "create", "export"],
        "knowledge": ["view", "create", "edit", "delete", "publish"]
    }
    
    # 敏感操作
    SENSITIVE_OPERATIONS = [
        "user:delete", "role:delete", "system:config",
        "workflow:delete", "template:delete", "knowledge:delete"
    ]
    
    @classmethod
    async def init_system_roles(cls, db: AsyncSession) -> None:
        """初始化系统角色"""
        for code, role_data in cls.SYSTEM_ROLES.items():
            result = await db.execute(
                select(Role).where(Role.code == code)
            )
            if not result.scalar_one_or_none():
                role = Role(
                    name=role_data["name"],
                    code=role_data["code"],
                    description=role_data["description"],
                    is_system=role_data["is_system"],
                    permissions=role_data["permissions"]
                )
                db.add(role)
        
        await db.commit()
    
    @classmethod
    async def create_user(
        cls,
        username: str,
        email: str,
        password: str,
        full_name: str,
        organization_id: Optional[int] = None,
        role_ids: Optional[List[int]] = None,
        db: AsyncSession = None
    ) -> User:
        """创建用户"""
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            organization_id=organization_id,
            is_active=True
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # 分配角色
        if role_ids:
            for role_id in role_ids:
                user_role = UserRole(user_id=user.id, role_id=role_id)
                db.add(user_role)
            await db.commit()
        
        return user
    
    @classmethod
    async def assign_roles(
        cls,
        user_id: int,
        role_ids: List[int],
        organization_id: Optional[int] = None,
        db: AsyncSession
    ) -> bool:
        """分配角色"""
        # 删除现有角色
        await db.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        
        # 添加新角色
        for role_id in role_ids:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                organization_id=organization_id
            )
            db.add(user_role)
        
        await db.commit()
        return True
    
    @classmethod
    async def check_permission(
        cls,
        user_id: int,
        permission: str,
        db: AsyncSession
    ) -> bool:
        """检查用户权限"""
        # 查询用户及其角色
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return False
        
        # 超级管理员
        if user.is_superuser:
            return True
        
        # 查询用户角色
        result = await db.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user_id)
        )
        roles = result.scalars().all()
        
        for role in roles:
            perms = role.permissions or []
            
            # 完全匹配
            if permission in perms:
                return True
            
            # 通配符匹配
            for perm in perms:
                if perm == "*":
                    return True
                if perm.endswith(":*"):
                    prefix = perm[:-2]
                    if permission.startswith(prefix + ":"):
                        return True
        
        return False
    
    @classmethod
    async def recommend_roles(
        cls,
        user_info: Dict[str, Any],
        organization_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """智能推荐角色"""
        from app.core.ai_digital_base.gateway import ai_gateway
        
        system_prompt = """你是一个权限管理专家。根据用户信息，智能推荐合适的角色。

考虑因素：
- 用户的职位和部门
- 业务场景
- 最小权限原则

输出JSON格式：
{
    "recommended_roles": [
        {"role_code": "manager", "reason": "因为是部门经理"}
    ],
    "additional_permissions": ["权限1", "权限2"],
    "warnings": ["警告1"]
}"""
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"用户信息: {json.dumps(user_info, ensure_ascii=False)}"
        )
        
        if "error" in result:
            return []
        
        try:
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except:
            return []
    
    @classmethod
    async def detect_anomaly(
        cls,
        user_id: int,
        operation: str,
        context: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """异常行为检测"""
        # 获取用户历史行为
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {"anomaly": False}
        
        # 检查是否为敏感操作
        is_sensitive = operation in cls.SENSITIVE_OPERATIONS
        
        # 检查登录时间异常
        last_login = user.last_login
        login_hour = last_login.hour if last_login else 0
        unusual_time = login_hour < 6 or login_hour > 23
        
        # 检查登录频率
        unusual_frequency = user.login_count > 100
        
        anomalies = []
        if is_sensitive:
            anomalies.append("执行敏感操作")
        if unusual_time:
            anomalies.append("异常时间登录")
        if unusual_frequency:
            anomalies.append("登录频率异常")
        
        return {
            "anomaly": len(anomalies) > 0,
            "risk_level": "high" if len(anomalies) >= 2 else "medium" if anomalies else "low",
            "details": anomalies,
            "recommendation": "建议审核" if anomalies else "正常"
        }
    
    @classmethod
    async def get_user_permissions(
        cls,
        user_id: int,
        db: AsyncSession
    ) -> List[str]:
        """获取用户所有权限"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        if user.is_superuser:
            return ["*"]
        
        result = await db.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user_id)
        )
        roles = result.scalars().all()
        
        permissions = set()
        for role in roles:
            permissions.update(role.permissions or [])
        
        return list(permissions)
    
    @classmethod
    async def audit_log(
        cls,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        detail: Optional[Dict[str, Any]],
        ip_address: Optional[str],
        db: AsyncSession
    ) -> None:
        """记录审计日志"""
        from app.models.ai import AuditLog
        
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail or {},
            ip_address=ip_address
        )
        db.add(log)
        await db.commit()


permission_service = PermissionService()
