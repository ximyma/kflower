# -*- coding: utf-8 -*-
"""
生成更多经典模板（第二批）- 政府和企业常用
"""
import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, r'D:\kflower\kflower-backend')

import app.models.user
import app.models.workflow
import app.models.ai
import app.models.permission

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.workflow import Template, Workflow

# 第二批经典模板 - 政府公文、档案管理、合同管理等
MORE_TEMPLATES = [
    # ===== 政府公文类 =====
    {
        "name": "公文发文审批单",
        "code": "doc_dispatch",
        "category": "general",
        "description": "政府机关和企事业单位公文发文审批",
        "modules": [{
            "name": "main",
            "label": "发文信息",
            "fields": [
                {"type": "text", "label": "发文编号", "name": "doc_no", "width": "50%"},
                {"type": "select", "label": "发文类型", "name": "doc_type", "required": True, "width": "50%", "options": ["通知", "通报", "请示", "报告", "批复", "函", "纪要", "决定", "意见"]},
                {"type": "select", "label": "密级", "name": "security_level", "width": "50%", "options": ["公开", "内部", "秘密", "机密", "绝密"]},
                {"type": "select", "label": "紧急程度", "name": "urgency", "width": "50%", "options": ["平急", "加急", "特急", "特提"]},
                {"type": "text", "label": "发文机关", "name": "dispatch_org", "required": True, "width": "50%"},
                {"type": "text", "label": "签发人", "name": "signer", "width": "50%"},
                {"type": "text", "label": "主送机关", "name": "main_recipient", "required": True, "width": "100%"},
                {"type": "textarea", "label": "抄送机关", "name": "cc_recipient", "width": "100%"},
                {"type": "text", "label": "标题", "name": "title", "required": True, "width": "100%"},
                {"type": "richtext", "label": "正文内容", "name": "content", "required": True, "width": "100%"},
                {"type": "upload", "label": "附件", "name": "attachments", "width": "100%"},
                {"type": "date", "label": "成文日期", "name": "doc_date", "required": True, "width": "50%"},
                {"type": "number", "label": "印发份数", "name": "copies", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "收文登记处理单",
        "code": "doc_receive",
        "category": "general",
        "description": "收文登记、拟办、批办、承办全流程",
        "modules": [{
            "name": "main",
            "label": "收文信息",
            "fields": [
                {"type": "text", "label": "收文编号", "name": "receive_no", "width": "50%"},
                {"type": "date", "label": "收文日期", "name": "receive_date", "required": True, "width": "50%"},
                {"type": "select", "label": "收文类型", "name": "doc_type", "width": "50%", "options": ["上级来文", "平级来文", "下级来文", "其他来文"]},
                {"type": "select", "label": "密级", "name": "security_level", "width": "50%", "options": ["公开", "内部", "秘密", "机密", "绝密"]},
                {"type": "text", "label": "来文机关", "name": "from_org", "required": True, "width": "50%"},
                {"type": "text", "label": "来文字号", "name": "from_doc_no", "width": "50%"},
                {"type": "text", "label": "标题", "name": "title", "required": True, "width": "100%"},
                {"type": "date", "label": "来文日期", "name": "from_date", "width": "50%"},
                {"type": "number", "label": "来文份数", "name": "copies", "width": "50%"},
                {"type": "heading", "label": "拟办意见", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "拟办意见", "name": "proposed_opinion", "width": "100%"},
                {"type": "text", "label": "拟办人", "name": "proposed_by", "width": "50%"},
                {"type": "date", "label": "拟办日期", "name": "proposed_date", "width": "50%"},
                {"type": "heading", "label": "领导批示", "name": "h2", "width": "100%"},
                {"type": "textarea", "label": "领导批示", "name": "leader_instruction", "width": "100%"},
                {"type": "text", "label": "批示领导", "name": "leader_name", "width": "50%"},
                {"type": "date", "label": "批示日期", "name": "instruction_date", "width": "50%"},
                {"type": "heading", "label": "承办情况", "name": "h3", "width": "100%"},
                {"type": "textarea", "label": "承办结果", "name": "handle_result", "width": "100%"},
                {"type": "select", "label": "办理状态", "name": "handle_status", "width": "50%", "options": ["待办", "办理中", "已办结", "已归档"]},
                {"type": "date", "label": "办结日期", "name": "complete_date", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 合同管理类 =====
    {
        "name": "合同审批单",
        "code": "contract_approval",
        "category": "general",
        "description": "合同签订前的审批流程",
        "modules": [{
            "name": "main",
            "label": "合同信息",
            "fields": [
                {"type": "text", "label": "合同编号", "name": "contract_no", "width": "50%"},
                {"type": "text", "label": "合同名称", "name": "contract_name", "required": True, "width": "50%"},
                {"type": "select", "label": "合同类型", "name": "contract_type", "required": True, "width": "50%", "options": ["采购合同", "销售合同", "服务合同", "租赁合同", "劳动合同", "保密协议", "其他"]},
                {"type": "select", "label": "合同性质", "name": "contract_nature", "width": "50%", "options": ["新签", "续签", "变更", "补充"]},
                {"type": "text", "label": "甲方名称", "name": "party_a", "required": True, "width": "50%"},
                {"type": "text", "label": "乙方名称", "name": "party_b", "required": True, "width": "50%"},
                {"type": "daterange", "label": "合同期限", "name": "contract_period", "required": True, "width": "50%"},
                {"type": "money", "label": "合同金额", "name": "contract_amount", "required": True, "width": "50%"},
                {"type": "select", "label": "付款方式", "name": "payment_method", "width": "50%", "options": ["一次性付款", "分期付款", "按月付款", "按进度付款"]},
                {"type": "select", "label": "币种", "name": "currency", "width": "50%", "options": ["人民币", "美元", "欧元", "日元", "其他"]},
                {"type": "textarea", "label": "合同主要内容", "name": "main_content", "required": True, "width": "100%"},
                {"type": "textarea", "label": "主要条款", "name": "key_terms", "width": "100%"},
                {"type": "heading", "label": "审批信息", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "部门意见", "name": "dept_opinion", "width": "100%"},
                {"type": "textarea", "label": "法务意见", "name": "legal_opinion", "width": "100%"},
                {"type": "textarea", "label": "财务意见", "name": "finance_opinion", "width": "100%"},
                {"type": "textarea", "label": "领导批示", "name": "leader_opinion", "width": "100%"},
                {"type": "upload", "label": "合同附件", "name": "contract_file", "required": True, "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "合同台账登记表",
        "code": "contract_register",
        "category": "general",
        "description": "合同签订后的登记管理",
        "modules": [{
            "name": "main",
            "label": "合同信息",
            "fields": [
                {"type": "text", "label": "合同编号", "name": "contract_no", "required": True, "width": "50%"},
                {"type": "text", "label": "合同名称", "name": "contract_name", "required": True, "width": "50%"},
                {"type": "select", "label": "合同类型", "name": "contract_type", "required": True, "width": "50%", "options": ["采购合同", "销售合同", "服务合同", "租赁合同", "劳动合同", "其他"]},
                {"type": "select", "label": "合同状态", "name": "contract_status", "width": "50%", "options": ["执行中", "已到期", "已终止", "已续签"]},
                {"type": "text", "label": "甲方", "name": "party_a", "required": True, "width": "50%"},
                {"type": "text", "label": "乙方", "name": "party_b", "required": True, "width": "50%"},
                {"type": "date", "label": "签订日期", "name": "sign_date", "required": True, "width": "50%"},
                {"type": "date", "label": "生效日期", "name": "effective_date", "required": True, "width": "50%"},
                {"type": "date", "label": "到期日期", "name": "expiry_date", "required": True, "width": "50%"},
                {"type": "money", "label": "合同金额", "name": "contract_amount", "required": True, "width": "50%"},
                {"type": "money", "label": "已付款金额", "name": "paid_amount", "width": "50%"},
                {"type": "money", "label": "未付款金额", "name": "unpaid_amount", "width": "50%"},
                {"type": "number", "label": "付款进度(%)", "name": "payment_progress", "width": "50%"},
                {"type": "select", "label": "归档状态", "name": "archive_status", "width": "50%", "options": ["已归档", "未归档"]},
                {"type": "text", "label": "档案编号", "name": "archive_no", "width": "50%"},
                {"type": "textarea", "label": "备注", "name": "remark", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 资产管理类 =====
    {
        "name": "固定资产领用单",
        "code": "asset_borrow",
        "category": "inventory",
        "description": "固定资产领用申请和登记",
        "modules": [{
            "name": "main",
            "label": "领用信息",
            "fields": [
                {"type": "text", "label": "领用单号", "name": "borrow_no", "width": "50%"},
                {"type": "date", "label": "领用日期", "name": "borrow_date", "required": True, "width": "50%"},
                {"type": "text", "label": "领用人", "name": "borrower", "required": True, "width": "50%"},
                {"type": "select", "label": "领用部门", "name": "dept", "required": True, "width": "50%"},
                {"type": "heading", "label": "资产信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "资产编号", "name": "asset_no", "required": True, "width": "50%"},
                {"type": "text", "label": "资产名称", "name": "asset_name", "required": True, "width": "50%"},
                {"type": "select", "label": "资产类别", "name": "asset_category", "required": True, "width": "50%", "options": ["电脑设备", "办公设备", "通讯设备", "家具", "车辆", "其他"]},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "number", "label": "数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "text", "label": "单位", "name": "unit", "width": "50%", "options": ["台", "套", "件", "个"]},
                {"type": "textarea", "label": "领用事由", "name": "reason", "required": True, "width": "100%"},
                {"type": "heading", "label": "审批信息", "name": "h2", "width": "100%"},
                {"type": "text", "label": "部门负责人", "name": "dept_manager", "width": "50%"},
                {"type": "text", "label": "资产管理员", "name": "asset_manager", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "固定资产报废单",
        "code": "asset_scrap",
        "category": "inventory",
        "description": "固定资产报废申请",
        "modules": [{
            "name": "main",
            "label": "报废信息",
            "fields": [
                {"type": "text", "label": "报废单号", "name": "scrap_no", "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "apply_date", "required": True, "width": "50%"},
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "申请部门", "name": "dept", "required": True, "width": "50%"},
                {"type": "heading", "label": "资产信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "资产编号", "name": "asset_no", "required": True, "width": "50%"},
                {"type": "text", "label": "资产名称", "name": "asset_name", "required": True, "width": "50%"},
                {"type": "select", "label": "资产类别", "name": "asset_category", "required": True, "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "date", "label": "购置日期", "name": "purchase_date", "width": "50%"},
                {"type": "money", "label": "原值", "name": "original_value", "width": "50%"},
                {"type": "money", "label": "净值", "name": "net_value", "width": "50%"},
                {"type": "heading", "label": "报废信息", "name": "h2", "width": "100%"},
                {"type": "select", "label": "报废原因", "name": "scrap_reason", "required": True, "width": "50%", "options": ["使用年限到期", "技术淘汰", "损坏无法修复", "丢失", "其他"]},
                {"type": "textarea", "label": "报废说明", "name": "scrap_description", "required": True, "width": "100%"},
                {"type": "image", "label": "资产照片", "name": "asset_photo", "width": "50%"},
                {"type": "heading", "label": "审批信息", "name": "h3", "width": "100%"},
                {"type": "textarea", "label": "技术鉴定意见", "name": "technical_opinion", "width": "100%"},
                {"type": "textarea", "label": "部门意见", "name": "dept_opinion", "width": "100%"},
                {"type": "textarea", "label": "领导审批", "name": "leader_approval", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 培训管理类 =====
    {
        "name": "培训申请表",
        "code": "training_request",
        "category": "hr",
        "description": "员工培训申请",
        "modules": [{
            "name": "main",
            "label": "培训信息",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "dept", "required": True, "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "apply_date", "required": True, "width": "50%"},
                {"type": "select", "label": "培训类型", "name": "training_type", "required": True, "width": "50%", "options": ["内部培训", "外部培训", "在线课程", "会议研讨", "资格认证"]},
                {"type": "text", "label": "培训名称", "name": "training_name", "required": True, "width": "100%"},
                {"type": "text", "label": "培训机构", "name": "training_org", "width": "50%"},
                {"type": "daterange", "label": "培训时间", "name": "training_period", "required": True, "width": "50%"},
                {"type": "number", "label": "培训天数", "name": "training_days", "width": "50%"},
                {"type": "text", "label": "培训地点", "name": "training_location", "width": "50%"},
                {"type": "money", "label": "培训费用", "name": "training_fee", "width": "50%"},
                {"type": "textarea", "label": "培训内容", "name": "training_content", "required": True, "width": "100%"},
                {"type": "textarea", "label": "申请理由", "name": "apply_reason", "required": True, "width": "100%"},
                {"type": "textarea", "label": "预期收益", "name": "expected_benefit", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "培训效果评估表",
        "code": "training_eval",
        "category": "hr",
        "description": "培训后的效果评估",
        "modules": [{
            "name": "main",
            "label": "评估信息",
            "fields": [
                {"type": "text", "label": "培训名称", "name": "training_name", "required": True, "width": "50%"},
                {"type": "text", "label": "参训人员", "name": "trainee", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "dept", "width": "50%"},
                {"type": "date", "label": "评估日期", "name": "eval_date", "required": True, "width": "50%"},
                {"type": "heading", "label": "满意度评价", "name": "h1", "width": "100%"},
                {"type": "rate", "label": "培训内容满意度", "name": "content_satisfaction", "required": True, "width": "50%"},
                {"type": "rate", "label": "讲师水平满意度", "name": "trainer_satisfaction", "required": True, "width": "50%"},
                {"type": "rate", "label": "组织安排满意度", "name": "organization_satisfaction", "required": True, "width": "50%"},
                {"type": "rate", "label": "总体满意度", "name": "overall_satisfaction", "required": True, "width": "50%"},
                {"type": "heading", "label": "效果评估", "name": "h2", "width": "100%"},
                {"type": "select", "label": "知识掌握程度", "name": "knowledge_level", "width": "50%", "options": ["优秀", "良好", "一般", "较差"]},
                {"type": "select", "label": "技能提升程度", "name": "skill_level", "width": "50%", "options": ["显著提升", "有所提升", "无明显变化"]},
                {"type": "textarea", "label": "主要收获", "name": "main_gain", "width": "100%"},
                {"type": "textarea", "label": "改进建议", "name": "improvement_suggestions", "width": "100%"},
                {"type": "textarea", "label": "后续行动计划", "name": "action_plan", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 信访投诉类 =====
    {
        "name": "信访投诉登记表",
        "code": "petition_register",
        "category": "general",
        "description": "信访投诉事项登记",
        "modules": [{
            "name": "main",
            "label": "信访信息",
            "fields": [
                {"type": "text", "label": "信访编号", "name": "petition_no", "width": "50%"},
                {"type": "date", "label": "登记日期", "name": "register_date", "required": True, "width": "50%"},
                {"type": "select", "label": "信访类型", "name": "petition_type", "required": True, "width": "50%", "options": ["来信", "来访", "来电", "网上信访", "电子邮件"]},
                {"type": "select", "label": "信访性质", "name": "petition_nature", "width": "50%", "options": ["申诉", "求决", "揭发控告", "意见建议", "其他"]},
                {"type": "text", "label": "信访人姓名", "name": "petitioner_name", "required": True, "width": "50%"},
                {"type": "select", "label": "信访人性别", "name": "petitioner_gender", "width": "50%", "options": ["男", "女"]},
                {"type": "text", "label": "身份证号", "name": "id_card", "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "contact_phone", "width": "50%"},
                {"type": "textarea", "label": "联系地址", "name": "contact_address", "width": "100%"},
                {"type": "text", "label": "被反映人/单位", "name": "respondent", "width": "50%"},
                {"type": "textarea", "label": "信访内容", "name": "petition_content", "required": True, "width": "100%"},
                {"type": "heading", "label": "办理信息", "name": "h1", "width": "100%"},
                {"type": "select", "label": "办理状态", "name": "handle_status", "width": "50%", "options": ["待受理", "已受理", "办理中", "已办结", "已归档"]},
                {"type": "text", "label": "承办单位", "name": "handle_org", "width": "50%"},
                {"type": "textarea", "label": "办理结果", "name": "handle_result", "width": "100%"},
                {"type": "switch", "label": "是否满意", "name": "is_satisfied", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 档案管理类 =====
    {
        "name": "档案借阅申请单",
        "code": "archive_borrow",
        "category": "general",
        "description": "档案借阅申请",
        "modules": [{
            "name": "main",
            "label": "借阅信息",
            "fields": [
                {"type": "text", "label": "借阅单号", "name": "borrow_no", "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "apply_date", "required": True, "width": "50%"},
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "申请部门", "name": "dept", "required": True, "width": "50%"},
                {"type": "heading", "label": "档案信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "档案编号", "name": "archive_no", "required": True, "width": "50%"},
                {"type": "text", "label": "档案名称", "name": "archive_name", "required": True, "width": "50%"},
                {"type": "select", "label": "档案类别", "name": "archive_category", "required": True, "width": "50%", "options": ["文书档案", "人事档案", "财务档案", "项目档案", "合同档案", "其他"]},
                {"type": "select", "label": "密级", "name": "security_level", "width": "50%", "options": ["公开", "内部", "秘密", "机密"]},
                {"type": "date", "label": "借阅日期", "name": "borrow_date", "required": True, "width": "50%"},
                {"type": "date", "label": "归还日期", "name": "return_date", "required": True, "width": "50%"},
                {"type": "textarea", "label": "借阅目的", "name": "borrow_purpose", "required": True, "width": "100%"},
                {"type": "heading", "label": "审批信息", "name": "h2", "width": "100%"},
                {"type": "text", "label": "部门负责人", "name": "dept_manager", "width": "50%"},
                {"type": "text", "label": "档案管理员", "name": "archive_manager", "width": "50%"},
                {"type": "switch", "label": "是否外借", "name": "is_external", "width": "50%"}
            ]
        }],
        "is_published": True
    }
]


# 更多工作流
MORE_WORKFLOWS = [
    {
        "name": "合同审批流程",
        "code": "contract_approval_flow",
        "description": "合同签订前的多级审批流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交合同", "x": 300, "y": 100},
                {"id": "dept_review", "type": "task", "name": "部门审核", "x": 500, "y": 100},
                {"id": "legal_review", "type": "task", "name": "法务审核", "x": 500, "y": 300},
                {"id": "finance_review", "type": "task", "name": "财务审核", "x": 700, "y": 100},
                {"id": "ceo_approve", "type": "task", "name": "总经理审批", "x": 900, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1100, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "dept_review"},
                {"id": "e3", "source": "dept_review", "target": "legal_review"},
                {"id": "e4", "source": "legal_review", "target": "finance_review", "condition": "approved"},
                {"id": "e5", "source": "finance_review", "target": "ceo_approve", "condition": "large_amount"},
                {"id": "e6", "source": "finance_review", "target": "end", "condition": "small_amount"},
                {"id": "e7", "source": "ceo_approve", "target": "end"}
            ]
        },
        "is_published": True
    },
    {
        "name": "公文发文流程",
        "code": "doc_dispatch_flow",
        "description": "公文拟稿、审核、签发流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "draft", "type": "task", "name": "拟稿", "x": 300, "y": 100},
                {"id": "dept_check", "type": "task", "name": "部门核稿", "x": 500, "y": 100},
                {"id": "office_check", "type": "task", "name": "办公室审核", "x": 700, "y": 100},
                {"id": "leader_sign", "type": "task", "name": "领导签发", "x": 900, "y": 100},
                {"id": "print", "type": "task", "name": "排版印制", "x": 900, "y": 300},
                {"id": "dispatch", "type": "task", "name": "分发", "x": 1100, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1300, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "draft"},
                {"id": "e2", "source": "draft", "target": "dept_check"},
                {"id": "e3", "source": "dept_check", "target": "office_check"},
                {"id": "e4", "source": "office_check", "target": "leader_sign"},
                {"id": "e5", "source": "leader_sign", "target": "print"},
                {"id": "e6", "source": "print", "target": "dispatch"},
                {"id": "e7", "source": "dispatch", "target": "end"}
            ]
        },
        "is_published": True
    },
    {
        "name": "固定资产领用流程",
        "code": "asset_borrow_flow",
        "description": "固定资产申请、审批、领用流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交申请", "x": 300, "y": 100},
                {"id": "dept_approve", "type": "task", "name": "部门审批", "x": 500, "y": 100},
                {"id": "asset_review", "type": "task", "name": "资产审核", "x": 700, "y": 100},
                {"id": "issue", "type": "task", "name": "发放资产", "x": 900, "y": 100},
                {"id": "confirm", "type": "task", "name": "领用确认", "x": 1100, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1300, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "dept_approve"},
                {"id": "e3", "source": "dept_approve", "target": "asset_review", "condition": "approved"},
                {"id": "e4", "source": "asset_review", "target": "issue"},
                {"id": "e5", "source": "issue", "target": "confirm"},
                {"id": "e6", "source": "confirm", "target": "end"}
            ]
        },
        "is_published": True
    }
]


async def init_more_templates():
    """初始化更多模板"""
    async with AsyncSessionLocal() as db:
        print(f"Start importing {len(MORE_TEMPLATES)} more templates...")
        
        for template_data in MORE_TEMPLATES:
            from sqlalchemy import select
            result = await db.execute(
                select(Template).where(Template.code == template_data["code"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  Template exists: {template_data['name']}")
                continue
            
            template = Template(
                name=template_data["name"],
                code=template_data["code"],
                description=template_data["description"],
                category=template_data["category"],
                modules=template_data["modules"],
                is_published=template_data.get("is_published", True),
                is_template=True,
                created_by=1
            )
            db.add(template)
            print(f"  [OK] Created template: {template_data['name']}")
        
        await db.commit()
        print("Templates import completed!")


async def init_more_workflows():
    """初始化更多工作流"""
    async with AsyncSessionLocal() as db:
        print(f"\nStart importing {len(MORE_WORKFLOWS)} more workflows...")
        
        for workflow_data in MORE_WORKFLOWS:
            from sqlalchemy import select
            result = await db.execute(
                select(Workflow).where(Workflow.code == workflow_data["code"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  Workflow exists: {workflow_data['name']}")
                continue
            
            workflow = Workflow(
                name=workflow_data["name"],
                code=workflow_data["code"],
                description=workflow_data["description"],
                definition=workflow_data["definition"],
                flow_type="normal",
                created_by=1
            )
            db.add(workflow)
            print(f"  [OK] Created workflow: {workflow_data['name']}")
        
        await db.commit()
        print("Workflows import completed!")


async def main():
    """主函数"""
    print("=" * 60)
    print("Kflower More Templates and Workflows Import Tool")
    print("=" * 60)
    
    try:
        await init_more_templates()
        await init_more_workflows()
        print("\n" + "=" * 60)
        print("Import completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
