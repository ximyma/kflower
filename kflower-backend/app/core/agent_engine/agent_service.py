"""
智能体引擎 - 智能体服务
提供智能体对话、工具调用等核心功能
"""
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
import json
import uuid
from app.core.ai_digital_base.gateway import ai_gateway
from app.core.ai_digital_base.rag import rag_retriever
from app.core.agent_engine.tools import tool_registry, tool_executor
from app.core.agent_engine.orchestrator import agent_orchestrator, AgentType, Task
import logging

logger = logging.getLogger(__name__)


class AgentService:
    """
    智能体服务
    统一的智能体调用入口
    """
    
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        use_rag: bool = True,
        enable_tools: bool = True,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        智能体对话
        
        Args:
            message: 用户消息
            conversation_id: 会话ID
            context: 上下文信息（用户ID、租户ID等）
            use_rag: 是否使用RAG检索
            enable_tools: 是否启用工具调用
            model: 指定模型（可选）
            provider: 指定提供商（可选）
            
        Returns:
            对话响应
        """
        context = context or {}
        conversation_id = conversation_id or str(uuid.uuid4())
        
        # 初始化会话历史
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        history = self.conversation_history[conversation_id]
        
        # 构建消息列表
        messages = []
        
        # 系统提示词
        system_prompt = self._build_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        messages.extend(history[-10:])  # 保留最近10轮对话
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        # RAG检索增强
        rag_context = ""
        if use_rag:
            # 支持应用上下文感知的RAG检索
            if context and context.get("app_context"):
                # 使用应用上下文进行多集合检索
                relevant_docs = await rag_retriever.search_by_app_context(
                    app_context=context["app_context"],
                    query=message,
                    top_k=3
                )
            else:
                # 向后兼容：无应用上下文时使用默认集合
                relevant_docs = await rag_retriever.search(
                    collection_name="knowledge",
                    query=message,
                    top_k=3
                )
            
            if relevant_docs:
                rag_context = "\n\n相关上下文：\n" + "\n".join([
                    f"- {doc['text']}" for doc in relevant_docs
                ])
                messages[-1]["content"] += rag_context
        
        # 调用大模型前加载配置（强制重新加载以确保最新）
        await ai_gateway.load_config_from_db(force=True)
        
        # 调用大模型
        if enable_tools:
            # 带工具调用的对话
            response = await self._chat_with_tools(messages, context, model, provider)
        else:
            # 普通对话
            response = await ai_gateway.chat(messages, model=model, provider=provider)
        
        # 处理响应
        if "error" in response:
            return {
                "conversation_id": conversation_id,
                "response": f"抱歉，处理您的请求时出现问题：{response['error']}",
                "tool_calls": []
            }
        
        content = response.get("content", "")
        
        # 保存历史
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": content})
        
        return {
            "conversation_id": conversation_id,
            "response": content,
            "tool_calls": response.get("tool_calls", []),
            "usage": response.get("usage", {})
        }
    
    async def _chat_with_tools(
        self,
        messages: List[Dict],
        context: Dict[str, Any],
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """带工具调用的对话"""
        # 获取工具定义
        tools = tool_registry.get_tools_as_openai_format()
        
        # 第一次调用：可能触发工具调用
        response = await ai_gateway.chat(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            model=model,
            provider=provider
        )
        
        if "error" in response:
            return response
        
        # 检查是否有工具调用
        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            return response
        
        # 执行工具调用
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            
            # 执行工具
            result = await tool_executor.execute(tool_name, arguments, context)
            tool_results.append({
                "tool_call_id": tool_call.get("id"),
                "name": tool_name,
                "result": result
            })
            
            logger.info(f"Tool executed: {tool_name} -> {result}")
        
        # 将工具结果添加到消息
        messages.append({
            "role": "assistant",
            "content": response.get("content", ""),
            "tool_calls": tool_calls
        })
        
        for tr in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": tr["tool_call_id"],
                "name": tr["name"],
                "content": json.dumps(tr["result"])
            })
        
        # 第二次调用：基于工具结果生成最终回复
        final_response = await ai_gateway.chat(messages, model=model, provider=provider)
        
        return {
            "content": final_response.get("content", ""),
            "tool_calls": tool_results,
            "usage": final_response.get("usage", {})
        }
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """构建系统提示词"""
        user_name = context.get("user_name", "用户")
        tenant_name = context.get("tenant_name", "企业")
        
        return f"""你是 Kflower 企业智能管理平台的 AI 智能助手。

你具备以下能力：
1. 模板设计：帮助企业用户创建业务表单、数据模板
2. 数据查询：查询企业数据，生成统计报表
3. 流程管理：创建和管理工作流程
4. 知识问答：基于企业知识库回答问题

当前用户：{user_name}
所属企业：{tenant_name}

请用专业、友好的语气回答用户问题。如果需要执行操作，请使用提供的工具。
"""
    
    async def analyze_intent(
        self,
        message: str
    ) -> Dict[str, Any]:
        """分析用户意图"""
        intent_prompt = f"""分析以下用户消息的意图，返回JSON格式：

消息：{message}

请分析：
1. intent_type: 意图类型（create/query/update/delete/chat）
2. target: 目标对象（template/workflow/data/report/notification）
3. confidence: 置信度（0-1）
4. entities: 提取的实体列表

返回格式示例：
{{"intent_type": "create", "target": "template", "confidence": 0.9, "entities": ["客户管理"]}}
"""
        
        response = await ai_gateway.chat([
            {"role": "user", "content": intent_prompt}
        ])
        
        try:
            content = response.get("content", "{}")
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        except Exception:
            pass
        
        return {
            "intent_type": "chat",
            "target": None,
            "confidence": 0.5,
            "entities": []
        }
    
    async def generate_template(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """生成模板"""
        context = context or {}
        
        # 使用应用上下文感知的RAG检索
        if app_context:
            similar_templates = await rag_retriever.search_by_app_context(
                app_context=app_context,
                query=description,
                top_k=3
            )
        else:
            # 向后兼容
            similar_templates = await rag_retriever.search(
                collection_name="templates",
                query=description,
                top_k=3
            )
        
        # 构建提示词
        prompt = f"""根据以下描述生成一个业务模板配置：

描述：{description}

参考模板：
{json.dumps([t['text'] for t in similar_templates], ensure_ascii=False) if similar_templates else '无'}

请返回JSON格式的模板配置，包含：
- name: 模板名称
- description: 模板描述
- category: 分类
- fields: 字段列表，每个字段包含 name, type, required

示例：
{{
  "name": "客户管理",
  "description": "客户信息管理模板",
  "category": "CRM",
  "fields": [
    {{"name": "客户名称", "type": "string", "required": true}},
    {{"name": "联系人", "type": "string"}},
    {{"name": "电话", "type": "string"}},
    {{"name": "行业", "type": "dict"}}
  ]
}}
"""
        
        response = await ai_gateway.chat([
            {"role": "user", "content": prompt}
        ])
        
        try:
            content = response.get("content", "{}")
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                template_config = json.loads(json_match.group())
                
                # 创建模板
                result = await tool_executor.execute(
                    "create_template",
                    template_config,
                    context
                )
                
                return {
                    "success": True,
                    "template": template_config,
                    "created": result
                }
        except Exception as e:
            logger.error(f"Template generation error: {e}")
        
        return {
            "success": False,
            "error": "模板生成失败"
        }
    
    async def query_natural_language(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """自然语言查询数据"""
        # 分析查询意图
        intent = await self.analyze_intent(query)
        
        # 构建查询
        prompt = f"""将以下自然语言查询转换为数据库查询参数：

查询：{query}

请返回JSON格式：
{{"table": "表名", "conditions": {{"字段": "值"}}, "fields": ["返回字段"]}}

示例：
查询：查询所有北京的客户
返回：{{"table": "customers", "conditions": {{"city": "北京"}}, "fields": ["*"]}}
"""
        
        response = await ai_gateway.chat([
            {"role": "user", "content": prompt}
        ])
        
        try:
            content = response.get("content", "{}")
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                query_params = json.loads(json_match.group())
                
                # 执行查询
                result = await tool_executor.execute(
                    "query_data",
                    query_params,
                    context
                )
                
                return {
                    "success": True,
                    "query": query_params,
                    "data": result.get("result", {})
                }
        except Exception as e:
            logger.error(f"Query error: {e}")
        
        return {
            "success": False,
            "error": "查询失败"
        }


# 全局智能体服务实例
agent_service = AgentService()