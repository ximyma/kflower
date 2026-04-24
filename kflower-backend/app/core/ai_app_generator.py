"""
AI 复合应用生成引擎
从自然语言描述生成完整的业务应用
"""
from typing import Dict, Any, List, Optional
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AIAppGenerator:
    """
    AI 应用生成器
    
    从自然语言描述生成完整应用，包括：
    1. 分析用户需求，提取业务实体和流程
    2. 自动生成表单模板
    3. 自动生成工作流
    4. 建立表单关系
    5. 生成仪表盘
    6. 创建专用智能体
    
    Example:
        generator = AIAppGenerator()
        result = await generator.generate_from_description(
            description="创建一个采购管理系统，包括采购申请、审批流程、供应商管理",
            db=db,
            user_id=1,
            organization_id=1
        )
    """
    
    def __init__(self):
        self.generation_steps = [
            ("analyze_requirement", "分析需求"),
            ("generate_templates", "生成模板"),
            ("generate_workflows", "生成工作流"),
            ("establish_relations", "建立关系"),
            ("generate_dashboard", "生成仪表盘"),
            ("create_agents", "创建智能体"),
            ("assemble_app", "组装应用"),
        ]
    
    async def generate_from_description(
        self,
        description: str,
        db: AsyncSession,
        user_id: int,
        organization_id: Optional[int] = None,
        app_name: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        从自然语言描述生成应用
        
        Args:
            description: 用户需求描述
            db: 数据库会话
            user_id: 创建者ID
            organization_id: 组织ID
            app_name: 应用名称（可选，从描述推断）
            options: 生成选项
                - skip_workflow: 跳过工作流生成
                - skip_dashboard: 跳过仪表盘生成
                - skip_agent: 跳过智能体创建
                - template_style: 表单风格（minimal/standard/detailed）
        
        Returns:
            {
                "success": bool,
                "app": {...},
                "templates": [...],
                "workflows": [...],
                "relations": [...],
                "dashboard": {...},
                "agents": [...],
                "errors": [...]
            }
        """
        result = {
            "success": True,
            "app": None,
            "templates": [],
            "workflows": [],
            "relations": [],
            "dashboard": None,
            "agents": [],
            "errors": [],
            "steps": {}
        }
        
        try:
            # ========== Step 1: 分析需求 ==========
            logger.info(f"[AIAppGenerator] 开始分析需求: {description[:100]}...")
            
            analysis = await self._analyze_requirement(description)
            result["steps"]["analyze_requirement"] = {
                "status": "completed",
                "result": analysis
            }
            
            # 推断应用名称
            if not app_name:
                app_name = analysis.get("app_name", "AI生成应用")
            
            app_code = f"ai_{uuid.uuid4().hex[:8]}"
            
            # ========== Step 2: 生成模板 ==========
            logger.info("[AIAppGenerator] 生成表单模板...")
            
            templates_spec = analysis.get("templates", [])
            generated_templates = []
            
            for template_spec in templates_spec:
                template = await self._generate_template(
                    spec=template_spec,
                    db=db,
                    user_id=user_id,
                )
                if template:
                    generated_templates.append(template)
            
            result["templates"] = generated_templates
            result["steps"]["generate_templates"] = {
                "status": "completed",
                "count": len(generated_templates)
            }
            
            # ========== Step 3: 生成工作流 ==========
            if not (options or {}).get("skip_workflow"):
                logger.info("[AIAppGenerator] 生成工作流...")
                
                workflows_spec = analysis.get("workflows", [])
                generated_workflows = []
                
                for wf_spec in workflows_spec:
                    workflow = await self._generate_workflow(
                        spec=wf_spec,
                        db=db,
                        user_id=user_id,
                    )
                    if workflow:
                        generated_workflows.append(workflow)
                
                result["workflows"] = generated_workflows
                result["steps"]["generate_workflows"] = {
                    "status": "completed",
                    "count": len(generated_workflows)
                }
            
            # ========== Step 4: 建立关系 ==========
            logger.info("[AIAppGenerator] 建立表单关系...")
            
            relations_spec = analysis.get("relations", [])
            generated_relations = []
            
            for rel_spec in relations_spec:
                relation = await self._establish_relation(
                    spec=rel_spec,
                    templates=generated_templates,
                    db=db,
                )
                if relation:
                    generated_relations.append(relation)
            
            result["relations"] = generated_relations
            result["steps"]["establish_relations"] = {
                "status": "completed",
                "count": len(generated_relations)
            }
            
            # ========== Step 5: 生成仪表盘 ==========
            if not (options or {}).get("skip_dashboard"):
                logger.info("[AIAppGenerator] 生成仪表盘...")
                
                dashboard = await self._generate_dashboard(
                    app_name=app_name,
                    templates=generated_templates,
                    analysis=analysis,
                )
                
                result["dashboard"] = dashboard
                result["steps"]["generate_dashboard"] = {
                    "status": "completed"
                }
            
            # ========== Step 6: 创建智能体 ==========
            if not (options or {}).get("skip_agent"):
                logger.info("[AIAppGenerator] 创建专用智能体...")
                
                agents_spec = analysis.get("agents", [])
                generated_agents = []
                
                for agent_spec in agents_spec:
                    agent = await self._create_agent(
                        spec=agent_spec,
                        app_name=app_name,
                        db=db,
                    )
                    if agent:
                        generated_agents.append(agent)
                
                result["agents"] = generated_agents
                result["steps"]["create_agents"] = {
                    "status": "completed",
                    "count": len(generated_agents)
                }
            
            # ========== Step 7: 组装应用 ==========
            logger.info("[AIAppGenerator] 组装应用...")
            
            app = await self._assemble_app(
                name=app_name,
                code=app_code,
                description=description,
                templates=generated_templates,
                workflows=result["workflows"],
                relations=generated_relations,
                dashboard=result["dashboard"],
                agents=result["agents"],
                db=db,
                user_id=user_id,
                organization_id=organization_id,
            )
            
            result["app"] = app
            result["steps"]["assemble_app"] = {
                "status": "completed",
                "app_id": app.get("id")
            }
            
            logger.info(f"[AIAppGenerator] 应用生成完成: {app_name} (ID: {app.get('id')})")
            
        except Exception as e:
            logger.error(f"[AIAppGenerator] 生成失败: {e}", exc_info=True)
            result["success"] = False
            result["errors"].append(str(e))
        
        return result
    
    async def _analyze_requirement(self, description: str) -> Dict[str, Any]:
        """
        使用 AI 分析用户需求，提取结构化信息
        """
        from app.core.ai_digital_base.gateway import ai_gateway
        
        system_prompt = """你是一个业务系统分析专家。请分析用户的业务需求描述，提取以下结构化信息：

1. app_name: 应用名称（简洁，不超过10个字）
2. templates: 需要创建的表单模板列表，每个模板包含：
   - name: 模板名称
   - code: 模板代码（英文，下划线分隔）
   - fields: 字段列表，每个字段包含：name(英文名), label(中文标签), type(类型), required(是否必填)
   - 字段类型可选：text, textarea, number, date, datetime, select, radio, checkbox, switch, email, phone, file, image
3. workflows: 工作流列表，每个包含：
   - name: 工作流名称
   - trigger_template: 触发的模板代码
   - trigger_event: 触发事件（create/update）
   - nodes: 节点列表，每个节点：type(start/approval/end), name, approver_role(审批人角色)
4. relations: 表单关系列表，每个包含：
   - source_template: 源模板代码
   - target_template: 目标模板代码
   - relation_type: 关系类型（one_to_many/many_to_many）
   - lookup_fields: 关联字段映射
5. agents: 智能体列表，每个包含：
   - name: 智能体名称
   - type: 类型（assistant/analyst/qa）
   - description: 描述
6. dashboard: 仪表盘设计概要
   - kpis: KPI指标列表
   - charts: 图表列表

请以 JSON 格式返回结果，不要包含任何其他文本。"""

        try:
            response = await ai_gateway.chat_with_system_prompt(
                system_prompt=system_prompt,
                user_message=description
            )
            
            # 解析返回的 JSON
            content = response.get("content", "")
            
            # 提取 JSON（可能包裹在 ```json ... ``` 中）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            logger.error(f"AI 需求分析失败: {e}")
            # 返回默认结构
            return {
                "app_name": "AI生成应用",
                "templates": [],
                "workflows": [],
                "relations": [],
                "agents": [],
                "dashboard": {"kpis": [], "charts": []}
            }
    
    async def _generate_template(
        self,
        spec: Dict[str, Any],
        db: AsyncSession,
        user_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        根据规格创建模板
        """
        from app.models.workflow import Template
        
        try:
            template = Template(
                name=spec.get("name", "未命名模板"),
                code=f"tpl_{uuid.uuid4().hex[:8]}",
                description=spec.get("description", ""),
                config=spec.get("config", {}),  # fields存储在config中
                category=spec.get("category", "custom"),
                created_by=user_id,
            )
            
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            return {
                "id": template.id,
                "name": template.name,
                "code": template.code,
                "config": template.config,
            }
            
        except Exception as e:
            logger.error(f"生成模板失败: {e}")
            return None
    
    async def _generate_workflow(
        self,
        spec: Dict[str, Any],
        db: AsyncSession,
        user_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        生成工作流
        """
        from app.models.workflow import Workflow
        
        try:
            # 将节点规格转换为Workflow的nodes JSON格式
            nodes_spec = spec.get("nodes", [])
            nodes_json = []
            edges_json = []
            for idx, node_spec in enumerate(nodes_spec):
                node_id = f"node_{idx+1}"
                nodes_json.append({
                    "id": node_id,
                    "type": node_spec.get("type", "approval"),
                    "name": node_spec.get("name", f"节点{idx+1}"),
                    "config": {
                        "approver_role": node_spec.get("approver_role"),
                    },
                })
                # 连接边
                if idx > 0:
                    edges_json.append({
                        "source": f"node_{idx}",
                        "target": node_id,
                    })
            
            workflow = Workflow(
                name=spec.get("name", "未命名工作流"),
                nodes=nodes_json,
                edges=edges_json,
                variables=spec.get("variables", {}),
                created_by=user_id,
            )
            
            db.add(workflow)
            await db.commit()
            await db.refresh(workflow)
            
            return {
                "id": workflow.id,
                "name": workflow.name,
            }
            
        except Exception as e:
            logger.error(f"生成工作流失败: {e}")
            return None
    
    async def _establish_relation(
        self,
        spec: Dict[str, Any],
        templates: List[Dict[str, Any]],
        db: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
        """
        建立表单关系
        """
        from app.modules.my_apps.models import FormRelation
        
        try:
            # 查找源和目标模板
            source_code = spec.get("source_template")
            target_code = spec.get("target_template")
            
            source_id = None
            target_id = None
            
            for tpl in templates:
                if tpl.get("code") == source_code:
                    source_id = tpl.get("id")
                if tpl.get("code") == target_code:
                    target_id = tpl.get("id")
            
            if not source_id or not target_id:
                return None
            
            relation = FormRelation(
                app_id=0,  # 外部调用时设置
                source_template_id=source_id,
                target_template_id=target_id,
                relation_type=spec.get("relation_type", "one_to_many"),
                field_mapping=spec.get("lookup_fields", {}),
            )
            
            db.add(relation)
            await db.commit()
            
            return {
                "id": relation.id,
                "source": source_code,
                "target": target_code,
            }
            
        except Exception as e:
            logger.error(f"建立关系失败: {e}")
            return None
    
    async def _generate_dashboard(
        self,
        app_name: str,
        templates: List[Dict[str, Any]],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成仪表盘配置
        """
        dashboard_spec = analysis.get("dashboard", {})
        
        dashboard = {
            "name": f"{app_name}仪表盘",
            "pages": [
                {
                    "name": "概览",
                    "widgets": []
                }
            ],
            "kpis": dashboard_spec.get("kpis", []),
            "charts": dashboard_spec.get("charts", []),
        }
        
        # 为每个模板添加统计卡片
        for tpl in templates:
            dashboard["pages"][0]["widgets"].append({
                "type": "kpi",
                "title": f"{tpl['name']}总数",
                "data_source": {
                    "template_id": tpl["id"],
                    "aggregation": "count"
                }
            })
        
        return dashboard
    
    async def _create_agent(
        self,
        spec: Dict[str, Any],
        app_name: str,
        db: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
        """
        创建专用智能体
        """
        from app.models.ai import Agent
        
        try:
            agent = Agent(
                name=spec.get("name", f"{app_name}智能体"),
                agent_type=spec.get("type", "assistant"),
                description=spec.get("description", ""),
                system_prompt=f"你是{app_name}系统的{spec.get('name', '智能助手')}。",
                config={},
                is_active=True,
            )
            
            db.add(agent)
            await db.commit()
            await db.refresh(agent)
            
            return {
                "id": agent.id,
                "name": agent.name,
            }
            
        except Exception as e:
            logger.error(f"创建智能体失败: {e}")
            return None
    
    async def _assemble_app(
        self,
        name: str,
        code: str,
        description: str,
        templates: List[Dict[str, Any]],
        workflows: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
        dashboard: Dict[str, Any],
        agents: List[Dict[str, Any]],
        db: AsyncSession,
        user_id: int,
        organization_id: Optional[int],
    ) -> Dict[str, Any]:
        """
        组装应用
        """
        # 强制加载所有模型，解决 SQLAlchemy mapper 初始化顺序问题
        from app.models.user import User, Organization  # noqa: F401
        from app.models.workflow import Template, Workflow  # noqa: F401
        from app.modules.my_apps.models import Application, AppMenu
        
        try:
            # 创建应用
            app = Application(
                name=name,
                code=code,
                description=description,
                is_published=False,
                is_public=False,
                created_by=user_id,
                organization_id=organization_id,
                workflow_ids=[wf["id"] for wf in workflows],
                bound_agents=[{"agent_id": ag["id"]} for ag in agents],
                config={
                    "dashboard": dashboard,
                },
            )
            
            db.add(app)
            await db.flush()
            
            # 创建菜单
            for idx, tpl in enumerate(templates):
                menu = AppMenu(
                    app_id=app.id,
                    name=tpl["name"],
                    menu_type="template",
                    template_id=tpl["id"],
                    order=idx,
                )
                db.add(menu)
            
            # 更新关系的 app_id
            for rel in relations:
                if rel:
                    await db.execute(
                        """
                        UPDATE form_relations SET app_id = :app_id 
                        WHERE id = :rel_id
                        """,
                        {"app_id": app.id, "rel_id": rel["id"]}
                    )
            
            await db.commit()
            await db.refresh(app)
            
            return {
                "id": app.id,
                "name": app.name,
                "code": app.code,
            }
            
        except Exception as e:
            logger.error(f"组装应用失败: {e}")
            raise


# 全局实例
_ai_app_generator = None

def get_ai_app_generator() -> AIAppGenerator:
    """获取 AI 应用生成器实例"""
    global _ai_app_generator
    if _ai_app_generator is None:
        _ai_app_generator = AIAppGenerator()
    return _ai_app_generator
