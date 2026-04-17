"""
业务服务 - 模板设计服务
AI智能生成引擎
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.models.workflow import Template, TemplateInstance
from app.core.ai_digital_base.inference import inference_service


class TemplateService:
    """模板设计服务 - AI智能生成"""
    
    # 预定义的模块模板库
    MODULE_TEMPLATES = {
        "basic_info": {
            "name": "基本信息",
            "fields": [
                {"name": "名称", "type": "text", "required": True},
                {"name": "编码", "type": "text", "required": True},
                {"name": "描述", "type": "textarea"},
                {"name": "状态", "type": "select", "options": ["启用", "禁用"]},
                {"name": "创建时间", "type": "datetime", "auto_now": True}
            ]
        },
        "contact": {
            "name": "联系信息",
            "fields": [
                {"name": "联系人", "type": "text"},
                {"name": "电话", "type": "phone"},
                {"name": "手机", "type": "mobile"},
                {"name": "邮箱", "type": "email"},
                {"name": "地址", "type": "textarea"}
            ]
        },
        "finance": {
            "name": "财务信息",
            "fields": [
                {"name": "银行账户", "type": "text"},
                {"name": "开户行", "type": "text"},
                {"name": "税号", "type": "text"},
                {"name": "开户银行", "type": "text"},
                {"name": "财务联系人", "type": "text"}
            ]
        },
        "approval": {
            "name": "审批信息",
            "fields": [
                {"name": "申请人", "type": "user"},
                {"name": "申请日期", "type": "date"},
                {"name": "审批人", "type": "user"},
                {"name": "审批状态", "type": "select", "options": ["待审批", "已批准", "已拒绝"]},
                {"name": "审批意见", "type": "textarea"}
            ]
        },
        "logistics": {
            "name": "物流信息",
            "fields": [
                {"name": "发货日期", "type": "date"},
                {"name": "收货地址", "type": "textarea"},
                {"name": "承运商", "type": "text"},
                {"name": "运单号", "type": "text"},
                {"name": "物流状态", "type": "select", "options": ["待发货", "运输中", "已签收"]}
            ]
        }
    }
    
    # 业务场景模板
    BUSINESS_TEMPLATES = {
        "crm": {
            "name": "客户管理(CRM)",
            "category": "客户管理",
            "modules": ["basic_info", "contact", "finance"]
        },
        "inventory": {
            "name": "库存管理",
            "category": "仓储物流",
            "modules": ["basic_info", "logistics", "approval"]
        },
        "purchase": {
            "name": "采购管理",
            "category": "采购供应",
            "modules": ["basic_info", "finance", "approval"]
        },
        "hr": {
            "name": "人力资源",
            "category": "人力资源",
            "modules": ["basic_info", "contact"]
        },
        "project": {
            "name": "项目管理",
            "category": "项目管理",
            "modules": ["basic_info", "approval"]
        },
        "sales": {
            "name": "销售管理",
            "category": "市场营销",
            "modules": ["basic_info", "contact", "finance"]
        }
    }
    
    @classmethod
    async def generate_template(
        cls,
        description: str,
        db: AsyncSession,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """AI生成模板"""
        # 分析需求
        analysis = await inference_service.analyze_intent(description)
        
        # 智能推荐模块
        recommended_modules = cls._recommend_modules(description)
        
        # 生成模板结构
        template_data = {
            "name": cls._extract_name(description) or "AI生成模板",
            "description": description,
            "category": cls._detect_category(description),
            "modules": recommended_modules,
            "ai_generated": True,
            "ai_prompt": description
        }
        
        # 保存模板
        template = Template(
            name=template_data["name"],
            code=f"tpl_{int(__import__('time').time())}",
            description=template_data["description"],
            category=template_data["category"],
            modules=template_data["modules"],
            ai_generated=True,
            ai_prompt=description,
            organization_id=organization_id,
            created_by=user_id
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return {
            "id": template.id,
            "name": template.name,
            "modules": template.modules,
            "analysis": analysis
        }
    
    @classmethod
    async def suggest_fields(
        cls,
        module_name: str,
        context: str
    ) -> List[Dict[str, Any]]:
        """智能推荐字段"""
        # 基于模块类型推荐
        module_lower = module_name.lower()
        
        for key, template in cls.MODULE_TEMPLATES.items():
            if key in module_lower or template["name"] in module_name:
                return template["fields"]
        
        # AI推荐
        result = await inference_service.suggest_fields(module_name, context)
        if "error" not in result:
            return result.get("fields", [])
        
        return cls.MODULE_TEMPLATES["basic_info"]["fields"]
    
    @classmethod
    async def optimize_template(
        cls,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化模板"""
        # 检查字段重复
        all_fields = []
        for module in template_data.get("modules", []):
            all_fields.extend([f["name"] for f in module.get("fields", [])])
        
        duplicates = [f for f in all_fields if all_fields.count(f) > 1]
        
        optimizations = []
        if duplicates:
            optimizations.append(f"发现重复字段: {', '.join(set(duplicates))}")
        
        # 建议添加常用字段
        missing_suggestions = []
        if "basic_info" not in str(template_data):
            missing_suggestions.append("建议添加'基本信息'模块")
        if "approval" not in str(template_data) and template_data.get("need_approval"):
            missing_suggestions.append("建议添加'审批信息'模块")
        
        return {
            "optimizations": optimizations,
            "missing_suggestions": missing_suggestions,
            "improved_template": template_data
        }
    
    @classmethod
    def _recommend_modules(cls, description: str) -> List[Dict[str, Any]]:
        """根据描述推荐模块"""
        desc_lower = description.lower()
        recommended = []
        
        # 关键词匹配
        keywords_map = {
            "crm": ["客户", "crm", "customer"],
            "contact": ["联系", "contact", "地址"],
            "finance": ["财务", "finance", "银行", "账户"],
            "approval": ["审批", "approval", "审核"],
            "logistics": ["物流", "logistics", "发货", "运输"]
        }
        
        for module_key, keywords in keywords_map.items():
            if any(kw in desc_lower for kw in keywords):
                if module_key in cls.MODULE_TEMPLATES:
                    module = cls.MODULE_TEMPLATES[module_key].copy()
                    module["fields"] = module["fields"].copy()
                    recommended.append(module)
        
        # 默认添加基本信息
        if not recommended:
            recommended.append(cls.MODULE_TEMPLATES["basic_info"].copy())
        
        return recommended
    
    @classmethod
    def _extract_name(cls, description: str) -> Optional[str]:
        """提取模板名称"""
        # 简单实现，实际应该用AI
        import re
        patterns = [
            r'我要一个?(.+?)系统',
            r'创建(.+?)管理',
            r'(.+?)管理系统'
        ]
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(1)
        return None
    
    @classmethod
    def _detect_category(cls, description: str) -> str:
        """检测分类"""
        desc_lower = description.lower()
        categories = {
            "客户管理": ["客户", "crm", "customer", "销售"],
            "人力资源": ["员工", "hr", "人力资源", "考勤", "绩效"],
            "采购供应": ["采购", "purchase", "供应商"],
            "仓储物流": ["库存", "inventory", "仓库", "物流"],
            "项目管理": ["项目", "project", "任务"],
            "市场营销": ["市场", "营销", "推广"]
        }
        for cat, keywords in categories.items():
            if any(kw in desc_lower for kw in keywords):
                return cat
        return "通用"


template_service = TemplateService()
