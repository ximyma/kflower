"""
插件管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.modules.my_apps.models import AppPlugin, Application
from app.modules.my_apps.plugin_executor import plugin_executor, PluginContext
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/plugins", tags=["插件管理"])


# ============ Pydantic 模型 ============
class PluginCreate(BaseModel):
    name: str
    trigger_event: str  # before_save, after_save, before_delete, after_delete, on_load
    target_template_id: Optional[int] = None
    script_code: str
    is_enabled: bool = True


class PluginUpdate(BaseModel):
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    target_template_id: Optional[int] = None
    script_code: Optional[str] = None
    is_enabled: Optional[bool] = None


class PluginTestRequest(BaseModel):
    mock_data: Optional[dict] = None


# ============ 代码片段 ============
@router.get("/snippets", response_model=BaseResponse)
async def get_plugin_snippets(current_user: User = Depends(get_current_user)):
    """获取插件代码片段库"""
    snippets = [
        {
            "name": "自动计算合计",
            "description": "订单保存后，自动计算订单明细的合计金额",
            "trigger": "after_save",
            "code": '''def after_save(context):
    """
    订单保存后自动计算合计
    """
    # 获取订单ID
    order_id = context.data.get('id')
    if not order_id:
        return
    
    # 查询订单明细（假设明细模板ID为456，关联字段为order_id）
    items = context.query_records(456, [
        {"field": "order_id", "op": "=", "value": order_id}
    ])
    
    # 计算合计
    total = sum(item.get('amount', 0) for item in items)
    
    # 更新订单主表
    context.update_record(context.template_id, order_id, {
        'total_amount': total
    })
    
    context.log(f"订单{order_id}合计已更新为{total}")
'''
        },
        {
            "name": "发送审批通知",
            "description": "提交审批时，通知审批人",
            "trigger": "after_save",
            "code": '''def after_save(context):
    """
    提交审批后通知审批人
    """
    assignee_id = context.data.get('assignee_id')
    title = context.data.get('title', '待审批')
    
    if assignee_id:
        context.send_notification(
            user_id=assignee_id,
            title=f"新的待审批: {title}",
            content=f"有一笔新的审批需要您处理"
        )
        context.log(f"已通知用户 {assignee_id}")
'''
        },
        {
            "name": "自动创建跟进记录",
            "description": "客户新建时自动创建首次跟进记录",
            "trigger": "after_save",
            "code": '''def after_save(context):
    """
    客户创建后自动创建跟进记录
    """
    customer_id = context.data.get('id')
    customer_name = context.data.get('name', '未知客户')
    
    # 跟进记录模板ID（需要替换为实际的模板ID）
    followup_template_id = 789
    
    # 创建首次跟进记录
    context.create_record(followup_template_id, {
        'customer_id': customer_id,
        'content': f'客户 {customer_name} 的首次跟进',
        'followup_date': datetime.now().strftime('%Y-%m-%d'),
        'followup_type': '首次接触'
    })
    
    context.log(f"已为客户 {customer_name} 创建首次跟进记录")
'''
        },
        {
            "name": "库存扣减",
            "description": "销售出库时自动扣减库存",
            "trigger": "after_save",
            "code": '''def after_save(context):
    """
    出库单保存后扣减库存
    """
    # 获取出库明细（假设明细模板ID为111）
    order_id = context.data.get('id')
    items = context.query_records(111, [
        {"field": "outbound_id", "op": "=", "value": order_id}
    ])
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        
        if product_id and quantity > 0:
            # 库存模板ID（假设为222）
            stock_tpl_id = 222
            
            # 查询当前库存
            stock_items = context.query_records(stock_tpl_id, [
                {"field": "product_id", "op": "=", "value": product_id}
            ], limit=1)
            
            if stock_items:
                current_stock = stock_items[0].get('stock', 0)
                new_stock = max(0, current_stock - quantity)
                context.update_record(stock_tpl_id, stock_items[0]['id'], {
                    'stock': new_stock
                })
    
    context.log(f"出库单 {order_id} 已更新库存")
'''
        },
        {
            "name": "数据验证",
            "description": "保存前验证数据合法性",
            "trigger": "before_save",
            "code": '''def before_save(context):
    """
    保存前验证数据
    """
    # 示例：验证金额不能为负数
    amount = context.data.get('amount', 0)
    if amount < 0:
        raise ValueError("金额不能为负数")
    
    # 示例：验证必填字段
    required_fields = ['name', 'customer_id']
    for field in required_fields:
        if not context.data.get(field):
            raise ValueError(f"字段 {field} 不能为空")
    
    context.log("数据验证通过")
'''
        }
    ]
    return BaseResponse(data=snippets)


# ============ 插件 CRUD ============
@router.get("/app/{app_id}", response_model=BaseResponse)
async def list_app_plugins(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用的所有插件"""
    result = await db.execute(
        select(AppPlugin).where(AppPlugin.app_id == app_id).order_by(AppPlugin.created_at.desc())
    )
    plugins = result.scalars().all()
    return BaseResponse(data=[
        {
            "id": p.id,
            "name": p.name,
            "trigger_event": p.trigger_event,
            "target_template_id": p.target_template_id,
            "is_enabled": p.is_enabled,
            "script_code": p.script_code,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in plugins
    ])


@router.post("/app/{app_id}", response_model=BaseResponse)
async def create_plugin(
    app_id: int,
    data: PluginCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建插件"""
    # 验证应用存在
    result = await db.execute(select(Application).where(Application.id == app_id))
    if not result.scalar_one_or_none():
        return BaseResponse(success=False, message="应用不存在")

    plugin = AppPlugin(
        app_id=app_id,
        name=data.name,
        trigger_event=data.trigger_event,
        target_template_id=data.target_template_id,
        script_code=data.script_code,
        is_enabled=data.is_enabled
    )
    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)

    return BaseResponse(message="插件创建成功", data={"id": plugin.id})


@router.get("/{plugin_id}", response_model=BaseResponse)
async def get_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取插件详情"""
    result = await db.execute(select(AppPlugin).where(AppPlugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        return BaseResponse(success=False, message="插件不存在")

    return BaseResponse(data={
        "id": plugin.id,
        "app_id": plugin.app_id,
        "name": plugin.name,
        "trigger_event": plugin.trigger_event,
        "target_template_id": plugin.target_template_id,
        "script_code": plugin.script_code,
        "is_enabled": plugin.is_enabled,
    })


@router.put("/{plugin_id}", response_model=BaseResponse)
async def update_plugin(
    plugin_id: int,
    data: PluginUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新插件"""
    result = await db.execute(select(AppPlugin).where(AppPlugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        return BaseResponse(success=False, message="插件不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plugin, key, value)

    await db.commit()

    return BaseResponse(message="插件更新成功")


@router.delete("/{plugin_id}", response_model=BaseResponse)
async def delete_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除插件"""
    result = await db.execute(select(AppPlugin).where(AppPlugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        return BaseResponse(success=False, message="插件不存在")

    await db.delete(plugin)
    await db.commit()

    return BaseResponse(message="插件删除成功")


@router.post("/{plugin_id}/test", response_model=BaseResponse)
async def test_plugin(
    plugin_id: int,
    test_data: PluginTestRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试插件执行"""
    result = await db.execute(select(AppPlugin).where(AppPlugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        return BaseResponse(success=False, message="插件不存在")

    # 构建测试上下文
    mock_data = test_data.mock_data if test_data else {"id": 1, "name": "测试数据"}

    context = PluginContext(
        data=mock_data,
        old_data=None,
        db=db,
        user_id=current_user.id,
        template_id=plugin.target_template_id or 0,
        event=plugin.trigger_event,
        app_id=plugin.app_id
    )

    # 执行插件
    exec_result = await plugin_executor.execute(plugin.script_code, context, timeout=10)

    return BaseResponse(
        data={
            "success": exec_result["success"],
            "output": exec_result.get("output"),
            "error": exec_result.get("error"),
        }
    )
