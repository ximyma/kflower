"""
AI 设计助手 - API 路由
根据自然语言需求生成应用设计方案
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.agent_engine.agent_service import agent_service
from app.models.user import User
from app.modules.my_apps.models import Application

router = APIRouter(prefix="/ai-design", tags=["AI设计助手"])


class GenerateDesignRequest(BaseModel):
    """生成设计方案请求"""
    app_id: int
    prompt: str


class ApplyDesignRequest(BaseModel):
    """应用设计方案请求"""
    app_name: Optional[str] = None
    description: Optional[str] = None
    templates: List[Any] = []
    relations: List[Any] = []
    plugins: List[Any] = []
    menus: List[Any] = []
    homepage: Optional[dict] = None


def _build_design_prompt(prompt: str) -> str:
    """构建发送给 AI 的设计提示词"""
    return f"""请根据以下需求设计一个业务应用，返回标准的JSON格式设计方案：

需求描述：
{prompt}

请返回以下格式的JSON（不要包含任何其他文字，只返回JSON）：
{{
  "app_name": "应用名称（用英文或拼音，4-20字符）",
  "description": "应用描述（10-50字）",
  "templates": [
    {{
      "name": "表单名称（用英文或拼音）",
      "description": "表单描述",
      "category": "分类（客户管理/订单管理/行政管理/项目管理/人力资源/财务管理/其他）",
      "fields": [
        {{
          "name": "字段名（英文或拼音）",
          "label": "显示名称",
          "type": "字段类型(text/number/select/date/datetime/textarea/switch/radio/checkbox/relation)",
          "required": true或false,
          "options": ["选项1", "选项2"]（仅select/radio/checkbox类型需要）
        }}
      ]
    }}
  ],
  "relations": [
    {{
      "from_template": "源表单名称",
      "to_template": "目标表单名称",
      "relation_type": "belongs_to/has_many",
      "field": "关联字段名"
    }}
  ],
  "plugins": [
    {{
      "name": "插件名称",
      "trigger_event": "before_save/after_save/on_load",
      "description": "插件功能描述"
    }}
  ],
  "menus": [
    {{
      "label": "菜单名称",
      "icon": "Element Plus图标名如Document/Folder/User/Setting等",
      "template_name": "关联的表单名称"
    }}
  ],
  "homepage": {{
    "type": "dashboard",
    "title": "主页标题",
    "widgets": [
      {{
        "type": "stat/list/chart",
        "title": "组件标题",
        "template_name": "数据源表单名称"
      }}
    ]
  }}
}}

重要要求：
1. JSON必须完全合法，可以用中文
2. templates数组至少包含1个表单，最多5个
3. 每个表单的fields数组至少包含3个字段
4. relation_type中belongs_to表示"属于"，has_many表示"拥有"
5. 返回的JSON中不要包含任何注释或说明文字
"""


@router.post("/generate")
async def generate_design(
    request: GenerateDesignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成设计方案
    
    根据用户输入的自然语言需求，调用 AI 生成应用设计方案
    """
    from sqlalchemy import select
    
    # 验证应用是否存在
    result = await db.execute(
        select(Application).where(
            Application.id == request.app_id,
            Application.created_by == current_user.id
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 构建发送给 AI 的提示词
    design_prompt = _build_design_prompt(request.prompt)
    
    try:
        # 调用 AI agent 生成设计方案
        context = {
            "user_id": current_user.id,
            "user_name": current_user.full_name or current_user.username,
            "app_id": request.app_id,
            "app_name": app.name,
        }
        
        result = await agent_service.chat(
            message=design_prompt,
            context=context,
            use_rag=False,
            enable_tools=False,
            model=None,
            provider=None
        )
        
        # 解析 AI 返回的内容
        content = ""
        if isinstance(result, dict):
            content = result.get("response") or result.get("message") or result.get("content") or str(result)
        elif isinstance(result, str):
            content = result
        else:
            content = str(result)
        
        # 提取 JSON
        import json
        import re
        
        design = None
        
        # 尝试从代码块中提取 JSON
        code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', content)
        if code_block_match:
            try:
                design = json.loads(code_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试直接解析整个内容
        if not design:
            # 找到第一个 { 和最后一个 }
            first_brace = content.find('{')
            last_brace = content.rfind('}')
            if first_brace >= 0 and last_brace > first_brace:
                json_str = content[first_brace:last_brace + 1]
                try:
                    design = json.loads(json_str)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"AI返回的JSON格式有误: {e}\n\n原始内容:\n{content[:1000]}"
                    )
        
        if not design:
            raise HTTPException(
                status_code=500,
                detail=f"无法从AI返回中解析设计方案\n\n原始内容:\n{content[:1000]}"
            )
        
        # 验证必要的字段
        if "templates" not in design or not design["templates"]:
            design["templates"] = []
        
        if "relations" not in design:
            design["relations"] = []
        
        if "plugins" not in design:
            design["plugins"] = []
        
        if "menus" not in design:
            design["menus"] = []
        
        if "homepage" not in design:
            design["homepage"] = {"type": "dashboard", "title": f"{design.get('app_name', '应用')}主页", "widgets": []}
        
        return {
            "success": True,
            "data": design
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"AI design generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI设计生成失败: {str(e)}")


@router.post("/apply/{app_id}")
async def apply_design(
    app_id: int,
    request: ApplyDesignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    应用设计方案
    
    将 AI 生成的设计方案应用到指定应用
    """
    from sqlalchemy import select
    from app.modules.my_apps.models import AppMenu
    from app.modules.my_apps.schemas import AppMenuCreate
    from app.modules.my_apps.service import my_apps_service
    from app.core.template_manager import template_manager
    
    # 验证应用是否存在
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.created_by == current_user.id
        )
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    created_templates = []
    created_relations = []
    errors = []
    
    # 1. 创建模板
    for tpl_data in request.templates:
        try:
            fields = tpl_data.get("fields", [])
            template_config = {
                "name": tpl_data.get("name"),
                "description": tpl_data.get("description", ""),
                "category": tpl_data.get("category", "其他"),
                "modules": [{
                    "name": tpl_data.get("name"),
                    "label": tpl_data.get("name"),
                    "fields": fields
                }],
                "config": {"fields": fields}
            }
            
            # 使用模板管理器创建模板
            template = await template_manager.create_template(
                db=db,
                data=template_config,
                user_id=current_user.id
            )
            
            created_templates.append({
                "name": tpl_data.get("name"),
                "id": template.id,
                "status": "created"
            })
            
            # 发布模板
            try:
                await template_manager.publish_template(db, template.id)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Publish template error: {e}")
                
        except Exception as e:
            errors.append(f"创建模板 {tpl_data.get('name')} 失败: {str(e)}")
    
    # 2. 创建关系
    for rel_data in request.relations:
        try:
            from_tpl = next((t for t in created_templates if t["name"] == rel_data.get("from_template")), None)
            to_tpl = next((t for t in created_templates if t["name"] == rel_data.get("to_template")), None)
            
            if from_tpl and to_tpl:
                relation_data = {
                    "from_template_id": from_tpl["id"],
                    "from_field_name": rel_data.get("field", "id"),
                    "to_template_id": to_tpl["id"],
                    "relation_type": rel_data.get("relation_type", "belongs_to")
                }
                relation = await my_apps_service.add_relation(db, app_id, relation_data)
                created_relations.append(relation)
        except Exception as e:
            errors.append(f"创建关系 {rel_data.get('from_template')} -> {rel_data.get('to_template')} 失败: {str(e)}")
    
    # 3. 创建菜单
    for menu_data in request.menus:
        try:
            template = next((t for t in created_templates if t["name"] == menu_data.get("template_name")), None)
            
            if template:
                menu = AppMenu(
                    app_id=app_id,
                    template_id=template["id"],
                    menu_label=menu_data.get("label", ""),
                    menu_icon=menu_data.get("icon", "Document"),
                    menu_order=len(request.menus) - list(request.menus).index(menu_data),
                    is_visible=True
                )
                db.add(menu)
                await db.flush()
        except Exception as e:
            errors.append(f"创建菜单 {menu_data.get('label')} 失败: {str(e)}")
    
    await db.commit()
    
    return {
        "success": True,
        "app_id": app_id,
        "templates": created_templates,
        "relations": [{"id": r.id, "name": f"{r.from_template_id} -> {r.to_template_id}"} for r in created_relations],
        "errors": errors if errors else None
    }
