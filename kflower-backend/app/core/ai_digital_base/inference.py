"""
AI数字底座 - 模型推理服务
封装各种AI模型调用，统一接口
"""
from typing import Dict, Any, Optional, List
from app.core.ai_digital_base.gateway import ai_gateway
from app.core.ai_digital_base.rag import rag_retriever


class InferenceService:
    """
    AI推理服务
    提供各种AI推理能力的统一入口
    """
    
    def __init__(self):
        self.gateway = ai_gateway
        self.rag = rag_retriever
    
    async def text_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """文本补全"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return await self.gateway.chat(messages, **kwargs)
    
    async def analyze_intent(self, text: str) -> Dict[str, Any]:
        """意图分析"""
        system_prompt = """你是一个意图分析助手。用户输入一段文本，你需要分析其意图。
请从以下类别中选择最合适的：
- template_design: 模板设计相关
- workflow: 流程审批相关
- data_query: 数据查询相关
- analysis: 决策分析相关
- permission: 权限管理相关
- system_setting: 系统设置相关
- general_chat: 日常聊天
- unknown: 无法识别

输出JSON格式：
{"intent": "类别", "confidence": 0.95, "entities": {"关键词": "值"}}"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"分析以下文本的意图：{text}"
        )
        
        if "error" in result:
            return {"intent": "unknown", "confidence": 0, "error": result["error"]}
        
        try:
            import json
            content = result["content"].strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            return {"intent": "unknown", "confidence": 0.5, "parse_error": str(e)}
        except Exception as e:
            return {"intent": "unknown", "confidence": 0.5, "error": str(e)}
    
    async def generate_template(self, description: str) -> Dict[str, Any]:
        """根据描述生成模板，返回可直接创建模板的完整结构化数据"""
        system_prompt = """你是一个低代码平台模板设计专家。用户描述一个业务需求，你需要生成对应的模板设计方案。

输出JSON格式，必须严格遵循以下结构：
{
    "template_name": "模板名称",
    "description": "模板描述",
    "category": "分类(如：人事管理/财务管理/项目管理/客户管理/行政管理/通用)",
    "modules": [
        {
            "name": "模块名称",
            "fields": [
                {"name": "字段名", "type": "字段类型", "required": true/false, "description": "描述", "options": ["选项1", "选项2"]}
            ]
        }
    ],
    "workflows": ["工作流名称列表"],
    "formulas": ["需要的公式列表"]
}

支持的字段类型（请根据实际需求选择合适的类型）：
- text: 单行文本
- number: 数字
- date: 日期
- select: 下拉选择（需要options）
- radio: 单选（需要options）
- checkbox: 多选（需要options）
- textarea: 多行文本
- email: 邮箱
- phone: 电话
- money: 金额
- url: 链接
- upload: 文件上传
- image: 图片
- switch: 开关
- rate: 评分
- richtext: 富文本
- subform: 子表单

注意：
1. options仅对select/radio/checkbox类型有效
2. 字段名应简洁专业
3. 每个模块字段数控制在3-15个
4. 根据业务场景合理设置required"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"设计一个满足以下需求的模板：{description}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            import json
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            return {"error": f"AI 返回的 JSON 格式无效: {str(e)}", "raw_content": result.get("content", "")[:500]}
        except Exception as e:
            return {"error": f"解析失败: {str(e)}", "raw_content": result.get("content", "")[:500]}
    
    async def suggest_fields(self, module_name: str, module_description: str) -> List[Dict]:
        """智能推荐字段"""
        system_prompt = f"""你是一个低代码平台字段设计专家。根据模块名称和描述，推荐合适的字段。

模块名称：{module_name}
模块描述：{module_description}

输出JSON数组格式：
[
    {{"name": "字段名", "type": "text/number/date/select/radio/checkbox", "required": true/false, "description": "字段说明"}}
]"""

        result = await self.gateway.chat(
            messages=[{"role": "user", "content": system_prompt}],
            temperature=0.3
        )
        
        if "error" in result:
            return []
        
        try:
            import json
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return []
        except Exception:
            return []
    
    async def explain_workflow(self, workflow_description: str) -> Dict[str, Any]:
        """解释和优化工作流"""
        system_prompt = """你是一个业务流程优化专家。分析并优化用户描述的工作流程。

输出JSON格式：
{
    "summary": "流程总结",
    "steps": ["步骤1", "步骤2", ...],
    "optimizations": ["优化建议1", "优化建议2", ...],
    "potential_bottlenecks": ["潜在瓶颈1", ...]
}"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"分析以下工作流程：{workflow_description}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            import json
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return {"summary": result["content"]}
        except Exception:
            return {"summary": result["content"]}
    
    async def generate_workflow(self, description: str) -> Dict[str, Any]:
        """根据描述生成工作流，返回可直接创建工作流的完整结构化数据"""
        system_prompt = """你是一个低代码平台工作流设计专家。用户描述一个业务流程需求，你需要生成对应的工作流设计方案。

输出JSON格式，必须严格遵循以下结构：
{
    "name": "工作流名称",
    "description": "工作流描述",
    "flow_type": "normal/approval/circulation",
    "nodes": [
        {
            "id": "node_1",
            "type": "start",
            "name": "开始",
            "config": {}
        },
        {
            "id": "node_2",
            "type": "task",
            "name": "任务节点名称",
            "config": {"assignee": "处理人/角色", "form_fields": ["字段1", "字段2"]}
        },
        {
            "id": "node_3",
            "type": "condition",
            "name": "条件判断",
            "config": {"conditions": [{"field": "字段", "operator": "eq/gt/lt/contains", "value": "值"}]}
        },
        {
            "id": "node_4",
            "type": "approval",
            "name": "审批节点名称",
            "config": {"approvers": ["审批人/角色"], "approval_type": "any/all"}
        },
        {
            "id": "node_5",
            "type": "end",
            "name": "结束",
            "config": {}
        }
    ],
    "edges": [
        {"id": "edge_1", "source": "node_1", "target": "node_2", "label": ""},
        {"id": "edge_2", "source": "node_2", "target": "node_3", "label": "提交"},
        {"id": "edge_3", "source": "node_3", "target": "node_4", "label": "条件满足"},
        {"id": "edge_4", "source": "node_3", "target": "node_2", "label": "条件不满足"},
        {"id": "edge_5", "source": "node_4", "target": "node_5", "label": "通过"}
    ]
}

节点类型说明：
- start: 开始节点（必须有且仅有一个）
- end: 结束节点（必须有且仅有一个）
- task: 任务节点（执行具体操作）
- condition: 条件判断节点（分支逻辑）
- approval: 审批节点（需要审批人确认）

注意事项：
1. 必须包含start和end节点
2. 节点id必须唯一，格式为node_N
3. 边的id必须唯一，格式为edge_N
4. source和target必须引用存在的节点id
5. condition节点至少需要两条出边（满足/不满足）
6. approval节点的approval_type: any(任一通过即可)/all(全部通过)
7. 根据业务场景合理设计流程，确保流程完整可执行"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"设计一个满足以下需求的工作流：{description}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            import json
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except Exception as e:
            return {"error": str(e), "raw_content": result["content"]}
    
    async def generate_chart_config(self, query: str, data_description: str) -> Dict[str, Any]:
        """生成图表配置"""
        system_prompt = """你是一个数据可视化专家。根据用户需求生成图表配置。

输出JSON格式：
{
    "chart_type": "line/bar/pie/scatter/funnel",
    "title": "图表标题",
    "x_axis": "X轴字段",
    "y_axis": ["Y轴字段列表"],
    "filters": ["筛选条件"],
    "color_scheme": "配色方案"
}"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"数据：{data_description}\n\n需求：{query}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            import json
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "AI 返回的 JSON 格式无效"}
        except Exception:
            return {"error": "解析失败"}
    
    async def generate_formula(self, description: str) -> str:
        """生成业务公式"""
        system_prompt = """你是一个低代码平台公式专家。根据描述生成公式。

支持的函数：SUM(), AVG(), COUNT(), IF(), VLOOKUP(), SUMIF(), COUNTIF(), CONCAT(), LEFT(), RIGHT(), DATE(), NOW()

输出格式：直接输出公式，不要其他解释"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"生成公式：{description}"
        )
        
        if "error" in result:
            return f"# 错误: {result['error']}"
        
        return result["content"].strip()
    
    async def analyze_data(self, query: str, data_context: str) -> Dict[str, Any]:
        """数据分析"""
        system_prompt = """你是一个数据分析专家。根据提供的数据上下文，回答用户的数据查询问题。
如果数据不足以回答，请明确说明需要什么额外信息。"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"数据上下文：\n{data_context}\n\n查询：{query}"
        )
        
        if "error" in result:
            return {"answer": f"分析失败: {result['error']}"}
        
        return {"answer": result["content"]}


# 全局推理服务实例
inference_service = InferenceService()
