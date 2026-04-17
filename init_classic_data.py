# -*- coding: utf-8 -*-
"""
生成经典模板和工作流到数据库
针对政府和企业常用场景
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# 添加后端路径
sys.path.insert(0, r'D:\kflower\kflower-backend')

# 先导入所有模型，确保关系正确
import app.models.user
import app.models.workflow
import app.models.ai
import app.models.permission

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.workflow import Template, Workflow

# 经典模板定义
CLASSIC_TEMPLATES = [
    # ===== 人力资源类 =====
    {
        "name": "员工入职登记表",
        "code": "emp_onboarding",
        "category": "hr",
        "description": "新员工入职信息登记，包含基本信息、联系方式、紧急联系人、银行账户等",
        "modules": [{
            "name": "main",
            "label": "入职信息",
            "fields": [
                {"type": "heading", "label": "基本信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "姓名", "name": "name", "required": True, "width": "50%"},
                {"type": "text", "label": "工号", "name": "employee_id", "required": True, "width": "50%"},
                {"type": "select", "label": "性别", "name": "gender", "required": True, "width": "50%", "options": ["男", "女"]},
                {"type": "date", "label": "出生日期", "name": "birthday", "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%", "options": ["技术部", "市场部", "财务部", "行政部", "人事部"]},
                {"type": "text", "label": "职位", "name": "position", "required": True, "width": "50%"},
                {"type": "date", "label": "入职日期", "name": "join_date", "required": True, "width": "50%"},
                {"type": "heading", "label": "联系方式", "name": "h2", "width": "100%"},
                {"type": "phone", "label": "手机号码", "name": "mobile", "required": True, "width": "50%"},
                {"type": "email", "label": "电子邮箱", "name": "email", "width": "50%"},
                {"type": "textarea", "label": "家庭住址", "name": "home_address", "width": "100%"},
                {"type": "heading", "label": "紧急联系人", "name": "h3", "width": "100%"},
                {"type": "text", "label": "联系人姓名", "name": "emergency_name", "width": "50%"},
                {"type": "phone", "label": "联系人电话", "name": "emergency_phone", "width": "50%"},
                {"type": "heading", "label": "银行账户", "name": "h4", "width": "100%"},
                {"type": "text", "label": "开户银行", "name": "bank_name", "width": "50%"},
                {"type": "text", "label": "银行账号", "name": "bank_account", "width": "50%"},
                {"type": "heading", "label": "附件上传", "name": "h5", "width": "100%"},
                {"type": "image", "label": "身份证正面", "name": "id_front", "width": "50%"},
                {"type": "image", "label": "身份证反面", "name": "id_back", "width": "50%"},
                {"type": "upload", "label": "学历证书", "name": "degree_cert", "width": "50%"},
                {"type": "upload", "label": "离职证明", "name": "resignation_letter", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "员工离职申请表",
        "code": "emp_resignation",
        "category": "hr",
        "description": "员工离职申请及交接清单",
        "modules": [{
            "name": "main",
            "label": "离职申请",
            "fields": [
                {"type": "text", "label": "姓名", "name": "name", "required": True, "width": "50%"},
                {"type": "text", "label": "工号", "name": "employee_id", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "text", "label": "职位", "name": "position", "width": "50%"},
                {"type": "date", "label": "入职日期", "name": "join_date", "width": "50%"},
                {"type": "date", "label": "预计离职日期", "name": "resign_date", "required": True, "width": "50%"},
                {"type": "select", "label": "离职类型", "name": "resign_type", "required": True, "width": "50%", "options": ["主动离职", "协商解除", "合同到期", "辞退", "其他"]},
                {"type": "textarea", "label": "离职原因", "name": "reason", "required": True, "width": "100%"},
                {"type": "heading", "label": "工作交接", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "交接事项", "name": "handover_items", "width": "100%"},
                {"type": "text", "label": "接手人", "name": "handover_to", "width": "50%"},
                {"type": "switch", "label": "物品已归还", "name": "items_returned", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "请假申请表",
        "code": "leave_request",
        "category": "hr",
        "description": "员工请假申请，支持事假、病假、年假等多种类型",
        "modules": [{
            "name": "main",
            "label": "请假申请",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "select", "label": "请假类型", "name": "leave_type", "required": True, "width": "50%", "options": ["事假", "病假", "年假", "婚假", "产假", "丧假", "调休", "其他"]},
                {"type": "date", "label": "开始日期", "name": "start_date", "required": True, "width": "50%"},
                {"type": "date", "label": "结束日期", "name": "end_date", "required": True, "width": "50%"},
                {"type": "number", "label": "请假天数", "name": "days", "required": True, "width": "50%"},
                {"type": "textarea", "label": "请假事由", "name": "reason", "required": True, "width": "100%"},
                {"type": "textarea", "label": "工作交接", "name": "work_handover", "width": "100%"},
                {"type": "text", "label": "紧急联系人", "name": "emergency_contact", "width": "50%"},
                {"type": "phone", "label": "紧急联系电话", "name": "emergency_phone", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 财务报销类 =====
    {
        "name": "费用报销单",
        "code": "expense_reimburse",
        "category": "finance",
        "description": "日常费用报销申请，包含交通费、餐饮费、住宿费等",
        "modules": [{
            "name": "main",
            "label": "报销信息",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "date", "label": "报销日期", "name": "expense_date", "required": True, "width": "50%"},
                {"type": "select", "label": "费用类型", "name": "expense_type", "required": True, "width": "50%", "options": ["交通费", "餐饮费", "住宿费", "办公用品", "通讯费", "差旅费", "业务招待费", "其他"]},
                {"type": "money", "label": "报销金额", "name": "amount", "required": True, "width": "50%"},
                {"type": "textarea", "label": "费用明细", "name": "details", "required": True, "width": "100%"},
                {"type": "textarea", "label": "报销事由", "name": "reason", "width": "100%"},
                {"type": "upload", "label": "发票附件", "name": "invoice", "width": "100%"},
                {"type": "select", "label": "支付方式", "name": "payment_method", "width": "50%", "options": ["银行转账", "现金", "支付宝", "微信"]},
                {"type": "text", "label": "收款账号", "name": "bank_account", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "差旅费报销单",
        "code": "travel_reimburse",
        "category": "finance",
        "description": "差旅费用报销，包含交通、住宿、餐饮等",
        "modules": [{
            "name": "main",
            "label": "差旅信息",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "text", "label": "出差事由", "name": "travel_reason", "required": True, "width": "50%"},
                {"type": "text", "label": "出差地点", "name": "destination", "required": True, "width": "50%"},
                {"type": "daterange", "label": "出差日期", "name": "travel_dates", "required": True, "width": "50%"},
                {"type": "number", "label": "出差天数", "name": "days", "width": "50%"},
                {"type": "heading", "label": "交通费用", "name": "h1", "width": "100%"},
                {"type": "money", "label": "去程交通费", "name": "transport_go", "width": "50%"},
                {"type": "money", "label": "返程交通费", "name": "transport_back", "width": "50%"},
                {"type": "heading", "label": "住宿餐饮", "name": "h2", "width": "100%"},
                {"type": "money", "label": "住宿费", "name": "accommodation", "width": "50%"},
                {"type": "money", "label": "餐饮补贴", "name": "meal_allowance", "width": "50%"},
                {"type": "heading", "label": "合计", "name": "h3", "width": "100%"},
                {"type": "money", "label": "报销总额", "name": "total_amount", "required": True, "width": "50%"},
                {"type": "upload", "label": "票据附件", "name": "receipts", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 采购供应链类 =====
    {
        "name": "供应商信息登记表",
        "code": "supplier_info",
        "category": "inventory",
        "description": "供应商基本信息、资质、联系方式登记",
        "modules": [{
            "name": "main",
            "label": "供应商信息",
            "fields": [
                {"type": "text", "label": "供应商名称", "name": "supplier_name", "required": True, "width": "100%"},
                {"type": "text", "label": "供应商编码", "name": "supplier_code", "required": True, "width": "50%"},
                {"type": "select", "label": "供应商类型", "name": "supplier_type", "required": True, "width": "50%", "options": ["原材料供应商", "设备供应商", "服务供应商", "物流供应商", "其他"]},
                {"type": "select", "label": "供应商等级", "name": "supplier_level", "width": "50%", "options": ["战略供应商", "核心供应商", "普通供应商", "临时供应商"]},
                {"type": "heading", "label": "联系方式", "name": "h1", "width": "100%"},
                {"type": "text", "label": "联系人", "name": "contact_person", "required": True, "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "contact_phone", "required": True, "width": "50%"},
                {"type": "email", "label": "电子邮箱", "name": "contact_email", "width": "50%"},
                {"type": "textarea", "label": "详细地址", "name": "address", "width": "100%"},
                {"type": "heading", "label": "资质信息", "name": "h2", "width": "100%"},
                {"type": "text", "label": "营业执照号", "name": "license_no", "width": "50%"},
                {"type": "date", "label": "有效期至", "name": "license_expiry", "width": "50%"},
                {"type": "upload", "label": "营业执照", "name": "license_file", "width": "50%"},
                {"type": "upload", "label": "资质证书", "name": "cert_file", "width": "50%"},
                {"type": "heading", "label": "银行账户", "name": "h3", "width": "100%"},
                {"type": "text", "label": "开户银行", "name": "bank_name", "width": "50%"},
                {"type": "text", "label": "银行账号", "name": "bank_account", "width": "50%"},
                {"type": "textarea", "label": "备注说明", "name": "remark", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "采购申请单",
        "code": "purchase_request",
        "category": "inventory",
        "description": "物资采购申请审批",
        "modules": [{
            "name": "main",
            "label": "采购申请",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "申请部门", "name": "department", "required": True, "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "request_date", "required": True, "width": "50%"},
                {"type": "select", "label": "紧急程度", "name": "urgency", "width": "50%", "options": ["普通", "紧急", "特急"]},
                {"type": "heading", "label": "采购物品", "name": "h1", "width": "100%"},
                {"type": "text", "label": "物品名称", "name": "item_name", "required": True, "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "number", "label": "数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "text", "label": "单位", "name": "unit", "width": "50%", "options": ["个", "件", "套", "台", "箱", "吨", "米", "升"]},
                {"type": "money", "label": "预估单价", "name": "estimated_price", "width": "50%"},
                {"type": "money", "label": "预估总价", "name": "estimated_total", "width": "50%"},
                {"type": "textarea", "label": "用途说明", "name": "purpose", "required": True, "width": "100%"},
                {"type": "textarea", "label": "推荐供应商", "name": "recommended_supplier", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 客户管理类 =====
    {
        "name": "客户信息登记表",
        "code": "customer_info",
        "category": "crm",
        "description": "客户基本信息、联系人、合作意向登记",
        "modules": [{
            "name": "main",
            "label": "客户信息",
            "fields": [
                {"type": "text", "label": "客户名称", "name": "customer_name", "required": True, "width": "100%"},
                {"type": "text", "label": "客户编码", "name": "customer_code", "width": "50%"},
                {"type": "select", "label": "客户类型", "name": "customer_type", "required": True, "width": "50%", "options": ["企业客户", "个人客户", "政府机构", "事业单位"]},
                {"type": "select", "label": "客户等级", "name": "customer_level", "width": "50%", "options": ["VIP客户", "重要客户", "普通客户", "潜在客户"]},
                {"type": "select", "label": "行业", "name": "industry", "width": "50%", "options": ["制造业", "零售业", "服务业", "科技业", "金融业", "教育", "医疗", "政府", "其他"]},
                {"type": "heading", "label": "联系信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "联系人", "name": "contact_person", "required": True, "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "contact_phone", "required": True, "width": "50%"},
                {"type": "email", "label": "电子邮箱", "name": "email", "width": "50%"},
                {"type": "textarea", "label": "详细地址", "name": "address", "width": "100%"},
                {"type": "heading", "label": "合作信息", "name": "h2", "width": "100%"},
                {"type": "select", "label": "合作状态", "name": "cooperation_status", "width": "50%", "options": ["意向", "洽谈中", "已签约", "合作中", "暂停", "终止"]},
                {"type": "textarea", "label": "合作意向", "name": "cooperation_intent", "width": "100%"},
                {"type": "textarea", "label": "备注", "name": "remark", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "客户投诉处理单",
        "code": "customer_complaint",
        "category": "crm",
        "description": "客户投诉登记及处理跟踪",
        "modules": [{
            "name": "main",
            "label": "投诉信息",
            "fields": [
                {"type": "text", "label": "投诉编号", "name": "complaint_no", "width": "50%"},
                {"type": "date", "label": "投诉日期", "name": "complaint_date", "required": True, "width": "50%"},
                {"type": "text", "label": "客户名称", "name": "customer_name", "required": True, "width": "50%"},
                {"type": "text", "label": "联系人", "name": "contact_person", "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "contact_phone", "width": "50%"},
                {"type": "select", "label": "投诉类型", "name": "complaint_type", "required": True, "width": "50%", "options": ["产品质量", "服务态度", "物流配送", "价格争议", "合同问题", "其他"]},
                {"type": "select", "label": "紧急程度", "name": "urgency", "width": "50%", "options": ["一般", "紧急", "特急"]},
                {"type": "textarea", "label": "投诉内容", "name": "complaint_content", "required": True, "width": "100%"},
                {"type": "upload", "label": "相关附件", "name": "attachments", "width": "100%"},
                {"type": "heading", "label": "处理信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "处理人", "name": "handler", "width": "50%"},
                {"type": "select", "label": "处理状态", "name": "status", "width": "50%", "options": ["待处理", "处理中", "已解决", "已关闭"]},
                {"type": "textarea", "label": "处理结果", "name": "handle_result", "width": "100%"},
                {"type": "date", "label": "完成日期", "name": "complete_date", "width": "50%"},
                {"type": "switch", "label": "客户满意", "name": "customer_satisfied", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 项目管理类 =====
    {
        "name": "项目立项申请表",
        "code": "project_application",
        "category": "project",
        "description": "新项目立项申请，包含项目背景、预算、计划等",
        "modules": [{
            "name": "main",
            "label": "项目信息",
            "fields": [
                {"type": "text", "label": "项目名称", "name": "project_name", "required": True, "width": "100%"},
                {"type": "text", "label": "项目编号", "name": "project_code", "width": "50%"},
                {"type": "select", "label": "项目类型", "name": "project_type", "required": True, "width": "50%", "options": ["研发项目", "市场项目", "IT项目", "基建项目", "其他"]},
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "所属部门", "name": "department", "required": True, "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "apply_date", "required": True, "width": "50%"},
                {"type": "heading", "label": "项目周期", "name": "h1", "width": "100%"},
                {"type": "date", "label": "计划开始日期", "name": "start_date", "width": "50%"},
                {"type": "date", "label": "计划结束日期", "name": "end_date", "width": "50%"},
                {"type": "heading", "label": "项目预算", "name": "h2", "width": "100%"},
                {"type": "money", "label": "项目预算", "name": "budget", "required": True, "width": "50%"},
                {"type": "textarea", "label": "预算明细", "name": "budget_detail", "width": "100%"},
                {"type": "heading", "label": "项目详情", "name": "h3", "width": "100%"},
                {"type": "textarea", "label": "项目背景", "name": "background", "required": True, "width": "100%"},
                {"type": "textarea", "label": "项目目标", "name": "objectives", "required": True, "width": "100%"},
                {"type": "textarea", "label": "预期成果", "name": "deliverables", "width": "100%"},
                {"type": "textarea", "label": "风险评估", "name": "risks", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "项目周报",
        "code": "project_weekly",
        "category": "project",
        "description": "项目周进度汇报",
        "modules": [{
            "name": "main",
            "label": "周报信息",
            "fields": [
                {"type": "text", "label": "项目名称", "name": "project_name", "required": True, "width": "50%"},
                {"type": "text", "label": "填报人", "name": "reporter", "required": True, "width": "50%"},
                {"type": "daterange", "label": "报告周期", "name": "report_period", "required": True, "width": "50%"},
                {"type": "heading", "label": "本周进展", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "已完成工作", "name": "completed_work", "required": True, "width": "100%"},
                {"type": "textarea", "label": "进行中工作", "name": "ongoing_work", "width": "100%"},
                {"type": "heading", "label": "下周计划", "name": "h2", "width": "100%"},
                {"type": "textarea", "label": "计划工作", "name": "planned_work", "required": True, "width": "100%"},
                {"type": "heading", "label": "问题与风险", "name": "h3", "width": "100%"},
                {"type": "textarea", "label": "遇到的问题", "name": "issues", "width": "100%"},
                {"type": "textarea", "label": "需要支持", "name": "support_needed", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 通用表单类 =====
    {
        "name": "会议纪要",
        "code": "meeting_minutes",
        "category": "general",
        "description": "会议记录及决议跟踪",
        "modules": [{
            "name": "main",
            "label": "会议信息",
            "fields": [
                {"type": "text", "label": "会议主题", "name": "meeting_topic", "required": True, "width": "100%"},
                {"type": "select", "label": "会议类型", "name": "meeting_type", "width": "50%", "options": ["周例会", "月度会议", "季度会议", "项目会议", "临时会议"]},
                {"type": "datetime", "label": "会议时间", "name": "meeting_time", "required": True, "width": "50%"},
                {"type": "text", "label": "会议地点", "name": "meeting_location", "width": "50%"},
                {"type": "text", "label": "主持人", "name": "host", "required": True, "width": "50%"},
                {"type": "text", "label": "记录人", "name": "recorder", "width": "50%"},
                {"type": "textarea", "label": "参会人员", "name": "attendees", "required": True, "width": "100%"},
                {"type": "heading", "label": "会议内容", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "会议议程", "name": "agenda", "width": "100%"},
                {"type": "textarea", "label": "讨论内容", "name": "discussion", "width": "100%"},
                {"type": "textarea", "label": "会议决议", "name": "resolutions", "width": "100%"},
                {"type": "textarea", "label": "行动项", "name": "action_items", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "用车申请单",
        "code": "vehicle_request",
        "category": "general",
        "description": "公务用车申请",
        "modules": [{
            "name": "main",
            "label": "用车信息",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "date", "label": "用车日期", "name": "use_date", "required": True, "width": "50%"},
                {"type": "select", "label": "用车类型", "name": "vehicle_type", "width": "50%", "options": ["公务用车", "商务接待", "会议用车", "其他"]},
                {"type": "text", "label": "出发地", "name": "departure", "required": True, "width": "50%"},
                {"type": "text", "label": "目的地", "name": "destination", "required": True, "width": "50%"},
                {"type": "textarea", "label": "用车事由", "name": "reason", "required": True, "width": "100%"},
                {"type": "number", "label": "乘车人数", "name": "passengers", "width": "50%"},
                {"type": "switch", "label": "需要司机", "name": "need_driver", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "印章使用申请单",
        "code": "seal_request",
        "category": "general",
        "description": "公章、合同章等印章使用申请",
        "modules": [{
            "name": "main",
            "label": "用印信息",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "request_date", "required": True, "width": "50%"},
                {"type": "select", "label": "印章类型", "name": "seal_type", "required": True, "width": "50%", "options": ["公章", "合同章", "财务章", "法人章", "发票章", "其他"]},
                {"type": "select", "label": "用印类型", "name": "usage_type", "required": True, "width": "50%", "options": ["文件盖章", "合同盖章", "证明盖章", "其他"]},
                {"type": "number", "label": "用印份数", "name": "copies", "required": True, "width": "50%"},
                {"type": "textarea", "label": "用印事由", "name": "reason", "required": True, "width": "100%"},
                {"type": "textarea", "label": "文件名称", "name": "document_name", "required": True, "width": "100%"},
                {"type": "upload", "label": "附件", "name": "attachments", "width": "100%"}
            ]
        }],
        "is_published": True
    }
]


# 经典工作流定义
CLASSIC_WORKFLOWS = [
    {
        "name": "请假审批流程",
        "code": "leave_approval",
        "category": "hr",
        "description": "员工请假申请审批流程，支持多级审批",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交请假申请", "x": 300, "y": 100, "assignee": "${applicant}"},
                {"id": "manager_approve", "type": "task", "name": "部门经理审批", "x": 500, "y": 100, "assignee": "${department_manager}"},
                {"id": "hr_approve", "type": "task", "name": "人事审批", "x": 700, "y": 100, "assignee": "${hr_manager}"},
                {"id": "end", "type": "end", "name": "结束", "x": 900, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "manager_approve"},
                {"id": "e3", "source": "manager_approve", "target": "hr_approve", "condition": "approved"},
                {"id": "e4", "source": "manager_approve", "target": "apply", "condition": "rejected"},
                {"id": "e5", "source": "hr_approve", "target": "end", "condition": "approved"},
                {"id": "e6", "source": "hr_approve", "target": "apply", "condition": "rejected"}
            ]
        },
        "is_published": True
    },
    {
        "name": "费用报销审批流程",
        "code": "expense_approval",
        "category": "finance",
        "description": "费用报销申请审批流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交报销单", "x": 300, "y": 100},
                {"id": "manager_approve", "type": "task", "name": "部门经理审批", "x": 500, "y": 100},
                {"id": "finance_approve", "type": "task", "name": "财务审批", "x": 700, "y": 100},
                {"id": "payment", "type": "task", "name": "出纳付款", "x": 700, "y": 300},
                {"id": "end", "type": "end", "name": "结束", "x": 900, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "manager_approve"},
                {"id": "e3", "source": "manager_approve", "target": "finance_approve", "condition": "approved"},
                {"id": "e4", "source": "manager_approve", "target": "apply", "condition": "rejected"},
                {"id": "e5", "source": "finance_approve", "target": "payment", "condition": "approved"},
                {"id": "e6", "source": "finance_approve", "target": "apply", "condition": "rejected"},
                {"id": "e7", "source": "payment", "target": "end"}
            ]
        },
        "is_published": True
    },
    {
        "name": "采购审批流程",
        "code": "purchase_approval",
        "category": "inventory",
        "description": "物资采购申请审批流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交采购申请", "x": 300, "y": 100},
                {"id": "manager_approve", "type": "task", "name": "部门经理审批", "x": 500, "y": 100},
                {"id": "procurement_approve", "type": "task", "name": "采购部审批", "x": 500, "y": 300},
                {"id": "finance_approve", "type": "task", "name": "财务审批", "x": 700, "y": 100},
                {"id": "ceo_approve", "type": "task", "name": "总经理审批", "x": 700, "y": 300},
                {"id": "purchase", "type": "task", "name": "执行采购", "x": 900, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1100, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "manager_approve"},
                {"id": "e3", "source": "manager_approve", "target": "procurement_approve"},
                {"id": "e4", "source": "procurement_approve", "target": "finance_approve"},
                {"id": "e5", "source": "finance_approve", "target": "ceo_approve", "condition": "amount > 10000"},
                {"id": "e6", "source": "finance_approve", "target": "purchase", "condition": "amount <= 10000"},
                {"id": "e7", "source": "ceo_approve", "target": "purchase"},
                {"id": "e8", "source": "purchase", "target": "end"}
            ]
        },
        "is_published": True
    },
    {
        "name": "项目立项审批流程",
        "code": "project_approval",
        "category": "project",
        "description": "新项目立项申请审批流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交立项申请", "x": 300, "y": 100},
                {"id": "dept_approve", "type": "task", "name": "部门负责人审批", "x": 500, "y": 100},
                {"id": "pmo_review", "type": "task", "name": "PMO评审", "x": 700, "y": 100},
                {"id": "finance_review", "type": "task", "name": "财务评审", "x": 700, "y": 300},
                {"id": "ceo_approve", "type": "task", "name": "总经理审批", "x": 900, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1100, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "dept_approve"},
                {"id": "e3", "source": "dept_approve", "target": "pmo_review", "condition": "approved"},
                {"id": "e4", "source": "pmo_review", "target": "finance_review"},
                {"id": "e5", "source": "finance_review", "target": "ceo_approve"},
                {"id": "e6", "source": "ceo_approve", "target": "end", "condition": "approved"}
            ]
        },
        "is_published": True
    },
    {
        "name": "印章使用审批流程",
        "code": "seal_approval",
        "category": "general",
        "description": "公章、合同章等印章使用审批流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交用印申请", "x": 300, "y": 100},
                {"id": "manager_approve", "type": "task", "name": "部门经理审批", "x": 500, "y": 100},
                {"id": "legal_review", "type": "task", "name": "法务审核", "x": 500, "y": 300},
                {"id": "seal_admin", "type": "task", "name": "印章管理员", "x": 700, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 900, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "manager_approve"},
                {"id": "e3", "source": "manager_approve", "target": "legal_review", "condition": "contract"},
                {"id": "e4", "source": "manager_approve", "target": "seal_admin", "condition": "not_contract"},
                {"id": "e5", "source": "legal_review", "target": "seal_admin"},
                {"id": "e6", "source": "seal_admin", "target": "end"}
            ]
        },
        "is_published": True
    }
]


async def init_classic_templates():
    """初始化经典模板"""
    async with AsyncSessionLocal() as db:
        print(f"Start importing {len(CLASSIC_TEMPLATES)} classic templates...")
        
        for template_data in CLASSIC_TEMPLATES:
            # 检查是否已存在
            from sqlalchemy import select
            result = await db.execute(
                select(Template).where(Template.code == template_data["code"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  Template exists: {template_data['name']}")
                continue
            
            # 创建新模板
            template = Template(
                name=template_data["name"],
                code=template_data["code"],
                description=template_data["description"],
                category=template_data["category"],
                modules=template_data["modules"],
                is_published=template_data.get("is_published", True),
                is_template=True,
                created_by=1  # admin
            )
            db.add(template)
            print(f"  [OK] 创建模板: {template_data['name']}")
        
        await db.commit()
        print("Templates import completed!")


async def init_classic_workflows():
    """初始化经典工作流"""
    async with AsyncSessionLocal() as db:
        print(f"\nStart importing {len(CLASSIC_WORKFLOWS)} classic workflows...")
        
        for workflow_data in CLASSIC_WORKFLOWS:
            # 检查是否已存在
            from sqlalchemy import select
            result = await db.execute(
                select(Workflow).where(Workflow.code == workflow_data["code"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  Workflow exists: {workflow_data['name']}")
                continue
            
            # 创建新工作流
            workflow = Workflow(
                name=workflow_data["name"],
                code=workflow_data["code"],
                description=workflow_data["description"],
                definition=workflow_data["definition"],
                flow_type="normal",
                created_by=1  # admin
            )
            db.add(workflow)
            print(f"  [OK] 创建工作流: {workflow_data['name']}")
        
        await db.commit()
        print("Workflows import completed!")


async def main():
    """主函数"""
    print("=" * 60)
    print("Kflower Classic Templates and Workflows Import Tool")
    print("=" * 60)
    
    try:
        await init_classic_templates()
        await init_classic_workflows()
        print("\n" + "=" * 60)
        print("Import completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
