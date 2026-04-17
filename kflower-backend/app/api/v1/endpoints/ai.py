"""
API路由 - AI对话模块
核心的AI对话入口，集成智能体引擎
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import uuid
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.ai_digital_base import (
    ai_gateway, conversation_manager, rag_retriever, inference_service
)
from app.core.agent_engine import agent_orchestrator, task_planner, AgentType
from app.models.user import User
from app.models.ai import AIConversation, AuditLog
from app.schemas.schemas import ChatRequest, ChatResponse, BaseResponse

router = APIRouter(prefix="/ai", tags=["AI智能"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI对话接口
    支持多种AI能力类型：general/template/workflow/analytics
    """
    # 先从数据库加载动态配置
    await ai_gateway.load_config_from_db(db)
    # 生成或获取对话ID
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # 添加用户消息
    conversation_manager.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        metadata={"user_id": current_user.id}
    )
    
    # 根据AI类型选择处理策略
    if request.ai_type == "general":
        response = await _handle_general_chat(conversation_id, request.message)
    elif request.ai_type == "template":
        response = await _handle_template_chat(conversation_id, request.message, request)
    elif request.ai_type == "workflow":
        response = await _handle_workflow_chat(conversation_id, request.message, request)
    elif request.ai_type == "analytics":
        response = await _handle_analytics_chat(conversation_id, request.message, request)
    else:
        response = await _handle_general_chat(conversation_id, request.message)
    
    # 添加AI回复
    conversation_manager.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=response["message"]
    )
    
    # 保存对话记录
    await _save_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        messages=conversation_manager.get_messages(conversation_id),
        ai_type=request.ai_type,
        related_type=request.related_type,
        related_id=request.related_id,
        organization_id=current_user.organization_id
    )
    
    return ChatResponse(
        conversation_id=conversation_id,
        message=response["message"],
        ai_type=request.ai_type,
        suggestions=response.get("suggestions", []),
        template_data=response.get("template_data"),
        workflow_data=response.get("workflow_data")
    )


async def _handle_general_chat(conversation_id: str, message: str) -> Dict[str, Any]:
    """处理通用对话"""
    # 获取对话历史
    messages = conversation_manager.get_history_for_ai(conversation_id, max_turns=10)
    
    # 调用AI
    result = await ai_gateway.chat(messages)
    
    if "error" in result:
        return {"message": f"抱歉，发生了错误：{result['error']}"}
    
    return {"message": result["content"], "suggestions": []}


async def _handle_template_chat(
    conversation_id: str,
    message: str,
    request: ChatRequest
) -> Dict[str, Any]:
    """处理模板设计对话"""
    # 分析用户意图
    intent = await inference_service.analyze_intent(message)
    
    if "generate" in message.lower() or "创建" in message or "设计" in message:
        # 生成模板
        result = await inference_service.generate_template(message)
        if "error" in result:
            return {"message": f"生成失败：{result['error']}"}
        
        message_text = f"我已经为您设计了「{result.get('template_name', '新模板')}」，包含以下模块：\n\n"
        for module in result.get("modules", []):
            message_text += f"📋 {module.get('name', '模块')}\n"
            for field in module.get("fields", [])[:5]:
                field_type = field.get('type', 'text')
                required_mark = " *" if field.get('required') else ""
                message_text += f"  - {field.get('name', '字段')}{required_mark}: {field_type}\n"
            if len(module.get("fields", [])) > 5:
                message_text += f"  ... 还有 {len(module['fields']) - 5} 个字段\n"
        
        message_text += "\n💡 点击下方按钮可直接创建此表单模板"
        
        # 构建可直接创建模板的template_data
        template_data = {
            "name": result.get("template_name", "未命名模板"),
            "description": result.get("description", ""),
            "category": result.get("category", "通用"),
            "ai_generated": True,
            "ai_prompt": message,
            "modules": [
                {
                    "name": mod.get("name", "未命名模块"),
                    "fields": [
                        {
                            "name": f.get("name", "未命名"),
                            "type": f.get("type", "text"),
                            "required": f.get("required", False),
                            "description": f.get("description", ""),
                            "options": f.get("options")
                        }
                        for f in mod.get("fields", [])
                    ]
                }
                for mod in result.get("modules", [])
            ]
        }
        
        return {
            "message": message_text,
            "suggestions": ["一键创建表单", "调整字段", "添加模块", "生成工作流"],
            "template_data": template_data
        }
    
    elif "字段" in message or "推荐" in message:
        # 推荐字段
        fields = await inference_service.suggest_fields("通用模块", message)
        if fields:
            message_text = "我为您推荐以下字段：\n\n"
            for field in fields[:8]:
                message_text += f"📝 {field.get('name', '字段')}\n"
                message_text += f"   类型: {field.get('type', 'text')}\n"
                message_text += f"   说明: {field.get('description', '无')}\n\n"
            
            # 也构建一个简易template_data，方便用户一键创建
            template_data = {
                "name": "推荐字段模板",
                "description": f"基于用户需求「{message}」生成的推荐字段模板",
                "category": "通用",
                "ai_generated": True,
                "ai_prompt": message,
                "modules": [
                    {
                        "name": "推荐字段模块",
                        "fields": [
                            {
                                "name": f.get("name", "未命名"),
                                "type": f.get("type", "text"),
                                "required": f.get("required", False),
                                "description": f.get("description", ""),
                                "options": f.get("options")
                            }
                            for f in fields[:15]
                        ]
                    }
                ]
            }
            
            return {
                "message": message_text,
                "suggestions": ["一键创建表单", "调整字段", "添加更多字段"],
                "template_data": template_data
            }
    
    # 默认通用对话
    return await _handle_general_chat(conversation_id, message)


async def _handle_workflow_chat(
    conversation_id: str,
    message: str,
    request: ChatRequest
) -> Dict[str, Any]:
    """处理流程审批对话"""
    if "设计" in message or "创建" in message or "流程" in message:
        # 设计工作流 - 使用generate_workflow获取结构化数据
        result = await inference_service.generate_workflow(message)
        if "error" in result:
            # 如果generate_workflow失败，回退到explain_workflow
            result = await inference_service.explain_workflow(message)
            if "error" in result:
                return {"message": f"设计失败：{result['error']}"}
            message_text = f"📋 流程分析结果：\n\n"
            message_text += f"**总结**：{result.get('summary', '')}\n\n"
            if result.get("steps"):
                message_text += "**步骤**：\n"
                for i, step in enumerate(result.get("steps", []), 1):
                    message_text += f"{i}. {step}\n"
            if result.get("optimizations"):
                message_text += "\n**优化建议**：\n"
                for opt in result.get("optimizations", []):
                    message_text += f"💡 {opt}\n"
            return {"message": message_text, "suggestions": ["优化流程", "添加审批节点", "执行测试"]}
        
        # 生成工作流文本描述
        message_text = f"我已经为您设计了「{result.get('name', '新工作流')}」工作流：\n\n"
        
        nodes = result.get("nodes", [])
        edges = result.get("edges", [])
        
        message_text += "**流程节点**：\n"
        for node in nodes:
            node_type_map = {
                "start": "🟢 开始", "end": "🔴 结束",
                "task": "📋 任务", "condition": "🔀 条件", "approval": "✅ 审批"
            }
            type_label = node_type_map.get(node.get("type", ""), node.get("type", ""))
            message_text += f"  {type_label}: {node.get('name', '')}\n"
            if node.get("config", {}).get("assignee"):
                message_text += f"    处理人: {node['config']['assignee']}\n"
            if node.get("config", {}).get("approvers"):
                message_text += f"    审批人: {', '.join(node['config']['approvers'])}\n"
        
        message_text += "\n💡 点击下方按钮可直接创建此工作流"
        
        # 构建可直接创建工作流的workflow_data
        workflow_data = {
            "name": result.get("name", "未命名工作流"),
            "description": result.get("description", ""),
            "flow_type": result.get("flow_type", "normal"),
            "nodes": [
                {
                    "id": node.get("id", ""),
                    "type": node.get("type", "task"),
                    "name": node.get("name", ""),
                    "config": node.get("config", {})
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge.get("id", ""),
                    "source": edge.get("source", ""),
                    "target": edge.get("target", ""),
                    "label": edge.get("label")
                }
                for edge in edges
            ]
        }
        
        return {
            "message": message_text,
            "suggestions": ["一键创建工作流", "优化流程", "添加审批节点", "执行测试"],
            "workflow_data": workflow_data
        }
    
    # 默认通用对话
    return await _handle_general_chat(conversation_id, message)


async def _handle_analytics_chat(
    conversation_id: str,
    message: str,
    request: ChatRequest
) -> Dict[str, Any]:
    """处理决策分析对话"""
    if "图表" in message or "可视化" in message:
        # 生成图表配置
        result = await inference_service.generate_chart_config(
            query=message,
            data_description="业务数据"
        )
        if "error" not in result:
            message_text = f"📊 图表配置建议：\n\n"
            message_text += f"**图表类型**：{result.get('chart_type', '折线图')}\n"
            message_text += f"**标题**：{result.get('title', '数据图表')}\n"
            message_text += f"**X轴**：{result.get('x_axis', '-')}\n"
            message_text += f"**Y轴**：{', '.join(result.get('y_axis', []))}\n"
            return {"message": message_text, "suggestions": ["调整图表", "查看数据", "导出报告"]}
    
    # 默认通用对话
    return await _handle_general_chat(conversation_id, message)


async def _save_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: int,
    messages: list,
    ai_type: str,
    related_type: str = None,
    related_id: int = None,
    organization_id: int = None
):
    """保存对话记录"""
    try:
        # 查找或创建对话记录
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.conversation_id == conversation_id,
                AIConversation.user_id == user_id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            conversation.messages = messages
            conversation.updated_at = __import__("datetime").datetime.now()
        else:
            conversation = AIConversation(
                conversation_id=conversation_id,
                user_id=user_id,
                messages=messages,
                ai_type=ai_type,
                related_type=related_type,
                related_id=related_id,
                organization_id=organization_id
            )
            db.add(conversation)
        
        await db.commit()
    except Exception as e:
        print(f"Save conversation error: {e}")


@router.get("/history")
async def get_chat_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话历史"""
    messages = conversation_manager.get_messages(conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}


@router.delete("/history/{conversation_id}")
async def delete_chat_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除对话"""
    conversation_manager.delete_conversation(conversation_id)
    
    # 删除数据库记录
    result = await db.execute(
        select(AIConversation).where(
            AIConversation.conversation_id == conversation_id,
            AIConversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        await db.delete(conversation)
        await db.commit()
    
    return BaseResponse(message="对话已删除")


@router.get("/providers")
async def list_ai_providers():
    """列出AI提供商"""
    providers = ai_gateway.list_providers()
    return {"providers": providers}
