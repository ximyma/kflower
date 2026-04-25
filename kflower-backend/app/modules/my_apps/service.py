"""
我的应用模块 - 业务逻辑服务层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from fastapi import HTTPException

from app.modules.my_apps.models import Application, AppMenu, FormRelation, AppPlugin
from app.modules.my_apps.schemas import (
    ApplicationCreate, ApplicationUpdate,
    AppMenuCreate, AppMenuUpdate,
    FormRelationCreate, FormRelationUpdate,
    AppPluginCreate, AppPluginUpdate,
    MenuTreeNode
)
from app.models.user import User


class MyAppsService:
    """我的应用服务层"""

    # ========== 应用 CRUD ==========
    @staticmethod
    async def create_app(db: AsyncSession, user: User, data: ApplicationCreate) -> Application:
        """创建应用"""
        code = f"app_{uuid.uuid4().hex[:8]}"
        app = Application(
            name=data.name,
            code=code,
            description=data.description,
            icon=data.icon,
            theme=data.theme,
            config=data.config or {},
            created_by=user.id,
            organization_id=getattr(user, 'organization_id', None),
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)
        return app

    @staticmethod
    async def get_apps(db: AsyncSession, user: User) -> List[Application]:
        """获取用户的应用列表"""
        query = select(Application).where(Application.created_by == user.id)
        result = await db.execute(query.order_by(Application.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_app(db: AsyncSession, app_id: int, user: User) -> Optional[dict]:
        """获取应用详情，返回 dict 避免 ORM lazy-load"""
        # 直接查询，不使用 selectinload（因为我们移除了跨模块关系定义）
        query = select(Application).where(
            Application.id == app_id,
            Application.created_by == user.id
        )
        result = await db.execute(query)
        app = result.scalar_one_or_none()
        if not app:
            return None

        # 单独查询关联数据
        menus_result = await db.execute(select(AppMenu).where(AppMenu.app_id == app_id))
        menus = menus_result.scalars().all()

        relations_result = await db.execute(select(FormRelation).where(FormRelation.app_id == app_id))
        relations = relations_result.scalars().all()

        plugins_result = await db.execute(select(AppPlugin).where(AppPlugin.app_id == app_id))
        plugins = plugins_result.scalars().all()

        return {
            "id": app.id,
            "code": app.code,
            "name": app.name,
            "description": app.description,
            "icon": app.icon,
            "theme": app.theme,
            "config": app.config,
            "is_published": app.is_published,
            "is_public": app.is_public,
            "created_by": app.created_by,
            "organization_id": app.organization_id,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            # 关联数据用 AppMenuSimple 手动构造，避免 children lazy-load
            "menus": [
                {
                    "id": m.id,
                    "app_id": m.app_id,
                    "parent_id": m.parent_id,
                    "template_id": m.template_id,
                    "menu_label": m.menu_label,
                    "menu_icon": m.menu_icon,
                    "menu_order": m.menu_order,
                    "is_visible": m.is_visible,
                    "list_page_config": m.list_page_config,
                    "form_page_config": m.form_page_config,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                }
                for m in menus  # 使用前面查询的 menus 变量
            ],
            "relations": [
                {
                    "id": r.id,
                    "app_id": r.app_id,
                    "from_template_id": r.from_template_id,
                    "from_field_name": r.from_field_name,
                    "to_template_id": r.to_template_id,
                    "relation_type": r.relation_type,
                    "display_field": r.display_field,
                    "on_delete": r.on_delete,
                    "reverse_name": r.reverse_name,
                    "created_at": r.created_at,
                }
                for r in relations  # 使用前面查询的 relations 变量
            ],
            "plugins": [
                {
                    "id": p.id,
                    "app_id": p.app_id,
                    "name": p.name,
                    "trigger_event": p.trigger_event,
                    "target_template_id": p.target_template_id,
                    "script_code": p.script_code,
                    "is_enabled": p.is_enabled,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                }
                for p in plugins  # 使用前面查询的 plugins 变量
            ],
        }

    @staticmethod
    async def update_app(db: AsyncSession, app: Application, data: ApplicationUpdate) -> Application:
        """更新应用"""
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(app, key, value)
        await db.commit()
        await db.refresh(app)
        return app

    @staticmethod
    async def delete_app(db: AsyncSession, app_id: int):
        """删除应用（级联删除菜单、关系、插件）"""
        # 先查询 ORM 对象
        query = select(Application).where(Application.id == app_id)
        result = await db.execute(query)
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="应用不存在")
        
        # 级联删除相关数据
        # 删除菜单
        menu_query = select(AppMenu).where(AppMenu.app_id == app_id)
        menu_result = await db.execute(menu_query)
        menus = menu_result.scalars().all()
        for menu in menus:
            await db.delete(menu)
        
        # 删除关系
        rel_query = select(FormRelation).where(FormRelation.app_id == app_id)
        rel_result = await db.execute(rel_query)
        relations = rel_result.scalars().all()
        for rel in relations:
            await db.delete(rel)
        
        # 删除插件
        plugin_query = select(AppPlugin).where(AppPlugin.app_id == app_id)
        plugin_query = select(AppPlugin).where(AppPlugin.app_id == app_id)
        plugin_result = await db.execute(plugin_query)
        plugins = plugin_result.scalars().all()
        for plugin in plugins:
            await db.delete(plugin)
        
        # 删除应用
        await db.delete(app)
        await db.commit()

    @staticmethod
    async def publish_app(db: AsyncSession, app_id: int) -> dict:
        """发布应用，返回 dict 避免 ORM lazy-load"""
        query = select(Application).where(Application.id == app_id)
        result = await db.execute(query)
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="应用不存在")
        app.is_published = True
        await db.commit()
        await db.refresh(app)
        return {
            "id": app.id,
            "code": app.code,
            "name": app.name,
            "description": app.description,
            "icon": app.icon,
            "theme": app.theme,
            "config": app.config,
            "is_published": app.is_published,
            "is_public": app.is_public,
            "created_by": app.created_by,
            "organization_id": app.organization_id,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
        }

    async def unpublish_app(db: AsyncSession, app_id: int) -> dict:
        """撤回应用（取消发布）"""
        query = select(Application).where(Application.id == app_id)
        result = await db.execute(query)
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="应用不存在")
        app.is_published = False
        await db.commit()
        await db.refresh(app)
        return {
            "id": app.id,
            "code": app.code,
            "name": app.name,
            "description": app.description,
            "icon": app.icon,
            "theme": app.theme,
            "config": app.config,
            "is_published": app.is_published,
            "is_public": app.is_public,
            "created_by": app.created_by,
            "organization_id": app.organization_id,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
        }

    # ========== 菜单管理 ==========
    @staticmethod
    async def add_menu(db: AsyncSession, app_id: int, data: AppMenuCreate) -> dict:
        """添加菜单，返回可安全序列化的 dict"""
        from datetime import datetime
        now = datetime.utcnow()
        # 处理 parent_id = 0 作为 None（前端使用 0 表示根菜单）
        parent_id = data.parent_id if data.parent_id and data.parent_id != 0 else None
        # 处理 template_id = 0 作为 None（允许创建没有模板的菜单）
        template_id = data.template_id if data.template_id and data.template_id != 0 else None
        # 处理 menu_label 为空的情况
        menu_label = data.menu_label or "未命名菜单"

        menu = AppMenu(
            app_id=app_id,
            parent_id=parent_id,
            template_id=template_id,
            menu_label=menu_label,
            menu_icon=data.menu_icon,
            menu_order=data.menu_order,
            is_visible=data.is_visible,
            list_page_config=data.list_page_config or {},
            form_page_config=data.form_page_config or {},
            created_at=now,
            updated_at=now,
        )
        db.add(menu)
        await db.commit()
        await db.refresh(menu)
        return {
            "id": menu.id,
            "app_id": menu.app_id,
            "parent_id": menu.parent_id,
            "template_id": menu.template_id,
            "menu_label": menu.menu_label,
            "menu_icon": menu.menu_icon,
            "menu_order": menu.menu_order,
            "is_visible": menu.is_visible,
            "list_page_config": menu.list_page_config,
            "form_page_config": menu.form_page_config,
            "created_at": menu.created_at or now,
            "updated_at": menu.updated_at or now,
        }

    @staticmethod
    async def update_menu(db: AsyncSession, menu: AppMenu, data: AppMenuUpdate) -> dict:
        """更新菜单，返回可安全序列化的 dict"""
        from datetime import datetime
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(menu, key, value)
        await db.commit()
        await db.refresh(menu)
        now = datetime.utcnow()
        return {
            "id": menu.id,
            "app_id": menu.app_id,
            "parent_id": menu.parent_id,
            "template_id": menu.template_id,
            "menu_label": menu.menu_label,
            "menu_icon": menu.menu_icon,
            "menu_order": menu.menu_order,
            "is_visible": menu.is_visible,
            "list_page_config": menu.list_page_config,
            "form_page_config": menu.form_page_config,
            "created_at": menu.created_at or now,
            "updated_at": menu.updated_at or now,
        }

    @staticmethod
    async def delete_menu(db: AsyncSession, menu: AppMenu):
        """删除菜单"""
        await db.delete(menu)
        await db.commit()

    @staticmethod
    async def get_menu_tree(db: AsyncSession, app_id: int) -> List[MenuTreeNode]:
        """获取菜单树"""
        result = await db.execute(
            select(AppMenu).where(AppMenu.app_id == app_id).order_by(AppMenu.menu_order)
        )
        menus = result.scalars().all()
        
        # 构建树形结构
        menu_map = {}
        root_menus = []
        
        for menu in menus:
            # 处理 template_id 为 None 的情况（文件夹类型菜单）
            template_id = menu.template_id
            path = f"/app/{app_id}/form/{template_id}" if template_id else None

            try:
                node = MenuTreeNode(
                    id=menu.id,
                    label=menu.menu_label or "未命名菜单",
                    icon=menu.menu_icon,
                    path=path,
                    template_id=template_id,
                    workflow_id=menu.workflow_id,
                    workflow_trigger=menu.workflow_trigger,
                    workflow_auto_approve=menu.workflow_auto_approve,
                    workflow_node_mapping=menu.workflow_node_mapping or [],
                    children=[]
                )
                menu_map[menu.id] = node

                if menu.parent_id is None:
                    root_menus.append(node)
                else:
                    parent = menu_map.get(menu.parent_id)
                    if parent:
                        parent.children.append(node)
            except Exception as e:
                # 记录错误但继续处理其他菜单
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"处理菜单 {menu.id} 时出错: {e}")
                continue
        
        return root_menus

    # ========== 表单关系管理 ==========
    @staticmethod
    async def add_relation(db: AsyncSession, app_id: int, data: FormRelationCreate) -> FormRelation:
        """添加表单关系"""
        relation = FormRelation(
            app_id=app_id,
            from_template_id=data.from_template_id,
            from_field_name=data.from_field_name,
            to_template_id=data.to_template_id,
            relation_type=data.relation_type,
            display_field=data.display_field,
            on_delete=data.on_delete,
            reverse_name=data.reverse_name,
        )
        db.add(relation)
        await db.commit()
        await db.refresh(relation)
        return relation

    @staticmethod
    async def get_relations(db: AsyncSession, app_id: int) -> List[FormRelation]:
        """获取应用的所有关系"""
        query = select(FormRelation).where(FormRelation.app_id == app_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def delete_relation(db: AsyncSession, relation: FormRelation):
        """删除关系"""
        await db.delete(relation)
        await db.commit()

    # ========== 插件管理 ==========
    @staticmethod
    async def add_plugin(db: AsyncSession, app_id: int, data: AppPluginCreate) -> AppPlugin:
        """添加插件"""
        plugin = AppPlugin(
            app_id=app_id,
            name=data.name,
            trigger_event=data.trigger_event,
            target_template_id=data.target_template_id,
            script_code=data.script_code,
            is_enabled=data.is_enabled,
        )
        db.add(plugin)
        await db.commit()
        await db.refresh(plugin)
        return plugin

    @staticmethod
    async def get_plugins(db: AsyncSession, app_id: int) -> List[AppPlugin]:
        """获取应用的插件列表"""
        query = select(AppPlugin).where(AppPlugin.app_id == app_id)
        result = await db.execute(query.order_by(AppPlugin.created_at))
        return result.scalars().all()

    @staticmethod
    async def update_plugin(db: AsyncSession, plugin: AppPlugin, data: AppPluginUpdate) -> AppPlugin:
        """更新插件"""
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plugin, key, value)
        await db.commit()
        await db.refresh(plugin)
        return plugin

    @staticmethod
    async def delete_plugin(db: AsyncSession, plugin: AppPlugin):
        """删除插件"""
        await db.delete(plugin)
        await db.commit()


my_apps_service = MyAppsService()
