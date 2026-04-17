"""
API路由 - 智能体服务
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.core.security import get_current_user
from app.core.agent_engine.agent_service import agent_service
from app.core.agent_engine.orchestrator import agent_orchestrator
from app.core.agent_engine.tools import tool_registry
from app.models.user import User

router = APIRouter(prefix="/agent", tags=["智能体"])


class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    conversation_id: Optional[str] = None
    use_rag: bool = True
    enable_tools: bool = True


class TemplateGenerateRequest(BaseModel):
    """模板生成请求"""
    description: str
    category: Optional[str] = None


class QueryRequest(BaseModel):
    """自然语言查询请求"""
    query: str


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    智能体对话
    
    与 AI 智能体进行对话，支持工具调用和 RAG 检索增强
    """
    context = {
        "user_id": current_user.id,
        "user_name": current_user.full_name or current_user.username,
        "tenant_id": getattr(current_user, 'tenant_id', None)
    }
    
    result = await agent_service.chat(
        message=request.message,
        conversation_id=request.conversation_id,
        context=context,
        use_rag=request.use_rag,
        enable_tools=request.enable_tools
    )
    
    return result


@router.post("/generate-template")
async def generate_template(
    request: TemplateGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI 生成模板
    
    根据自然语言描述生成业务模板
    """
    context = {
        "user_id": current_user.id,
        "user_name": current_user.full_name or current_user.username
    }
    
    result = await agent_service.generate_template(
        description=request.description,
        context=context
    )
    
    if result.get("success"):
        return {
            "message": "模板生成成功",
            "template": result.get("template"),
            "created": result.get("created")
        }
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "生成失败"))


@router.post("/query")
async def natural_language_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    自然语言查询数据
    
    使用自然语言查询企业数据
    """
    context = {
        "user_id": current_user.id,
        "user_name": current_user.full_name or current_user.username
    }
    
    result = await agent_service.query_natural_language(
        query=request.query,
        context=context
    )
    
    if result.get("success"):
        return {
            "query": request.query,
            "sql_params": result.get("query"),
            "data": result.get("data")
        }
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "查询失败"))


@router.get("/tools")
async def list_tools(
    tool_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    列出可用工具
    
    获取智能体可调用的工具列表
    """
    from app.core.agent_engine.tools.registry import ToolType
    
    type_filter = None
    if tool_type:
        try:
            type_filter = ToolType(tool_type)
        except:
            pass
    
    tools = tool_registry.list_tools(type_filter)
    
    return {
        "tools": tools,
        "count": len(tools)
    }


@router.get("/agents")
async def list_agents(
    current_user: User = Depends(get_current_user)
):
    """
    列出可用智能体
    
    获取平台注册的所有智能体
    """
    agents = agent_orchestrator.list_agents()
    
    return {
        "agents": agents,
        "count": len(agents)
    }


@router.get("/history")
async def get_task_history(
    count: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    获取任务历史
    
    获取智能体执行的任务历史记录
    """
    history = agent_orchestrator.get_task_history(count)
    
    return {
        "history": history,
        "count": len(history)
    }


@router.post("/analyze-intent")
async def analyze_intent(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    分析用户意图
    
    分析用户消息的意图类型
    """
    result = await agent_service.analyze_intent(request.query)
    
    return {
        "message": request.query,
        "intent": result
    }