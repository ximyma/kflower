# -*- coding: utf-8 -*-
"""
生成第三批经典模板 - 制造业、教育、医疗等行业
"""
import asyncio
import sys
sys.path.insert(0, r'D:\kflower\kflower-backend')

import app.models.user
import app.models.workflow
import app.models.ai
import app.models.permission

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.workflow import Template, Workflow
from sqlalchemy import select

# 第三批模板 - 行业专用
INDUSTRY_TEMPLATES = [
    # ===== 制造业 =====
    {
        "name": "生产计划单",
        "code": "production_plan",
        "category": "inventory",
        "description": "生产任务计划安排",
        "modules": [{
            "name": "main",
            "label": "生产信息",
            "fields": [
                {"type": "text", "label": "计划单号", "name": "plan_no", "width": "50%"},
                {"type": "date", "label": "计划日期", "name": "plan_date", "required": True, "width": "50%"},
                {"type": "text", "label": "产品名称", "name": "product_name", "required": True, "width": "50%"},
                {"type": "text", "label": "产品编号", "name": "product_code", "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "number", "label": "计划产量", "name": "plan_quantity", "required": True, "width": "50%"},
                {"type": "text", "label": "单位", "name": "unit", "width": "50%", "options": ["件", "个", "套", "台", "箱"]},
                {"type": "date", "label": "计划开工日期", "name": "start_date", "required": True, "width": "50%"},
                {"type": "date", "label": "计划完工日期", "name": "end_date", "required": True, "width": "50%"},
                {"type": "select", "label": "生产车间", "name": "workshop", "required": True, "width": "50%", "options": ["一车间", "二车间", "三车间", "装配车间", "包装车间"]},
                {"type": "text", "label": "生产线", "name": "production_line", "width": "50%"},
                {"type": "textarea", "label": "生产要求", "name": "requirements", "width": "100%"},
                {"type": "textarea", "label": "备注", "name": "remark", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "质量检验报告",
        "code": "quality_inspection",
        "category": "inventory",
        "description": "产品质量检验记录",
        "modules": [{
            "name": "main",
            "label": "检验信息",
            "fields": [
                {"type": "text", "label": "报告编号", "name": "report_no", "width": "50%"},
                {"type": "date", "label": "检验日期", "name": "inspect_date", "required": True, "width": "50%"},
                {"type": "text", "label": "产品名称", "name": "product_name", "required": True, "width": "50%"},
                {"type": "text", "label": "产品批次", "name": "batch_no", "required": True, "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "number", "label": "检验数量", "name": "inspect_quantity", "required": True, "width": "50%"},
                {"type": "select", "label": "检验类型", "name": "inspect_type", "required": True, "width": "50%", "options": ["来料检验", "过程检验", "成品检验", "出货检验"]},
                {"type": "select", "label": "检验结果", "name": "inspect_result", "required": True, "width": "50%", "options": ["合格", "不合格", "让步接收", "返工"]},
                {"type": "heading", "label": "检验项目", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "外观检验", "name": "appearance_check", "width": "100%"},
                {"type": "textarea", "label": "尺寸检验", "name": "dimension_check", "width": "100%"},
                {"type": "textarea", "label": "性能检验", "name": "performance_check", "width": "100%"},
                {"type": "textarea", "label": "不合格描述", "name": "defect_description", "width": "100%"},
                {"type": "number", "label": "不合格数量", "name": "defect_quantity", "width": "50%"},
                {"type": "text", "label": "检验员", "name": "inspector", "required": True, "width": "50%"},
                {"type": "image", "label": "检验照片", "name": "inspect_photos", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "设备维护保养单",
        "code": "equipment_maintenance",
        "category": "inventory",
        "description": "设备日常维护和保养记录",
        "modules": [{
            "name": "main",
            "label": "保养信息",
            "fields": [
                {"type": "text", "label": "保养单号", "name": "maint_no", "width": "50%"},
                {"type": "date", "label": "保养日期", "name": "maint_date", "required": True, "width": "50%"},
                {"type": "text", "label": "设备名称", "name": "equipment_name", "required": True, "width": "50%"},
                {"type": "text", "label": "设备编号", "name": "equipment_no", "required": True, "width": "50%"},
                {"type": "select", "label": "设备类型", "name": "equipment_type", "width": "50%", "options": ["生产设备", "检测设备", "辅助设备", "办公设备"]},
                {"type": "select", "label": "保养类型", "name": "maint_type", "required": True, "width": "50%", "options": ["日常保养", "一级保养", "二级保养", "大修"]},
                {"type": "select", "label": "保养周期", "name": "maint_cycle", "width": "50%", "options": ["每日", "每周", "每月", "每季度", "每年"]},
                {"type": "heading", "label": "保养内容", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "保养项目", "name": "maint_items", "required": True, "width": "100%"},
                {"type": "textarea", "label": "保养内容", "name": "maint_content", "required": True, "width": "100%"},
                {"type": "textarea", "label": "更换配件", "name": "replaced_parts", "width": "100%"},
                {"type": "textarea", "label": "异常情况", "name": "abnormal_condition", "width": "100%"},
                {"type": "heading", "label": "确认信息", "name": "h2", "width": "100%"},
                {"type": "text", "label": "保养人员", "name": "maint_staff", "required": True, "width": "50%"},
                {"type": "text", "label": "验收人员", "name": "acceptor", "width": "50%"},
                {"type": "switch", "label": "保养完成", "name": "is_completed", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 教育行业 =====
    {
        "name": "学生报名信息表",
        "code": "student_enrollment",
        "category": "general",
        "description": "新生入学报名登记",
        "modules": [{
            "name": "main",
            "label": "报名信息",
            "fields": [
                {"type": "text", "label": "姓名", "name": "name", "required": True, "width": "50%"},
                {"type": "select", "label": "性别", "name": "gender", "required": True, "width": "50%", "options": ["男", "女"]},
                {"type": "date", "label": "出生日期", "name": "birthday", "required": True, "width": "50%"},
                {"type": "text", "label": "身份证号", "name": "id_card", "required": True, "width": "50%"},
                {"type": "text", "label": "学籍号", "name": "student_no", "width": "50%"},
                {"type": "select", "label": "民族", "name": "ethnicity", "width": "50%", "options": ["汉族", "满族", "回族", "藏族", "维吾尔族", "其他"]},
                {"type": "heading", "label": "家庭信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "家长姓名", "name": "parent_name", "required": True, "width": "50%"},
                {"type": "phone", "label": "家长电话", "name": "parent_phone", "required": True, "width": "50%"},
                {"type": "textarea", "label": "家庭住址", "name": "home_address", "required": True, "width": "100%"},
                {"type": "heading", "label": "学籍信息", "name": "h2", "width": "100%"},
                {"type": "select", "label": "年级", "name": "grade", "required": True, "width": "50%", "options": ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]},
                {"type": "text", "label": "班级", "name": "class_name", "width": "50%"},
                {"type": "date", "label": "入学日期", "name": "enrollment_date", "width": "50%"},
                {"type": "select", "label": "学籍状态", "name": "status", "width": "50%", "options": ["在读", "休学", "转学", "毕业"]},
                {"type": "heading", "label": "附件", "name": "h3", "width": "100%"},
                {"type": "image", "label": "证件照", "name": "photo", "width": "50%"},
                {"type": "upload", "label": "户口本", "name": "household_register", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "学生成绩登记表",
        "code": "student_grade",
        "category": "general",
        "description": "学生考试成绩登记",
        "modules": [{
            "name": "main",
            "label": "成绩信息",
            "fields": [
                {"type": "text", "label": "学号", "name": "student_no", "required": True, "width": "50%"},
                {"type": "text", "label": "姓名", "name": "name", "required": True, "width": "50%"},
                {"type": "select", "label": "年级", "name": "grade", "required": True, "width": "50%"},
                {"type": "text", "label": "班级", "name": "class_name", "required": True, "width": "50%"},
                {"type": "select", "label": "学期", "name": "semester", "required": True, "width": "50%", "options": ["上学期", "下学期"]},
                {"type": "select", "label": "考试类型", "name": "exam_type", "required": True, "width": "50%", "options": ["期中考试", "期末考试", "月考", "模拟考试"]},
                {"type": "heading", "label": "各科成绩", "name": "h1", "width": "100%"},
                {"type": "number", "label": "语文", "name": "score_chinese", "width": "50%"},
                {"type": "number", "label": "数学", "name": "score_math", "width": "50%"},
                {"type": "number", "label": "英语", "name": "score_english", "width": "50%"},
                {"type": "number", "label": "物理", "name": "score_physics", "width": "50%"},
                {"type": "number", "label": "化学", "name": "score_chemistry", "width": "50%"},
                {"type": "number", "label": "生物", "name": "score_biology", "width": "50%"},
                {"type": "number", "label": "总分", "name": "total_score", "width": "50%"},
                {"type": "number", "label": "班级排名", "name": "class_rank", "width": "50%"},
                {"type": "number", "label": "年级排名", "name": "grade_rank", "width": "50%"},
                {"type": "textarea", "label": "教师评语", "name": "teacher_comment", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "课程安排表",
        "code": "course_schedule",
        "category": "general",
        "description": "学期课程安排",
        "modules": [{
            "name": "main",
            "label": "课程信息",
            "fields": [
                {"type": "text", "label": "课程编号", "name": "course_code", "required": True, "width": "50%"},
                {"type": "text", "label": "课程名称", "name": "course_name", "required": True, "width": "50%"},
                {"type": "select", "label": "课程类型", "name": "course_type", "required": True, "width": "50%", "options": ["必修课", "选修课", "公共课", "专业课", "实践课"]},
                {"type": "select", "label": "年级", "name": "grade", "required": True, "width": "50%"},
                {"type": "text", "label": "授课教师", "name": "teacher", "required": True, "width": "50%"},
                {"type": "text", "label": "上课班级", "name": "class_name", "width": "50%"},
                {"type": "select", "label": "星期", "name": "weekday", "required": True, "width": "50%", "options": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]},
                {"type": "time", "label": "开始时间", "name": "start_time", "required": True, "width": "50%"},
                {"type": "time", "label": "结束时间", "name": "end_time", "required": True, "width": "50%"},
                {"type": "text", "label": "上课地点", "name": "classroom", "width": "50%"},
                {"type": "number", "label": "学分", "name": "credits", "width": "50%"},
                {"type": "number", "label": "学时", "name": "hours", "width": "50%"},
                {"type": "textarea", "label": "课程简介", "name": "course_intro", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 医疗行业 =====
    {
        "name": "门诊挂号单",
        "code": "outpatient_register",
        "category": "general",
        "description": "患者门诊挂号登记",
        "modules": [{
            "name": "main",
            "label": "挂号信息",
            "fields": [
                {"type": "text", "label": "挂号单号", "name": "register_no", "width": "50%"},
                {"type": "date", "label": "挂号日期", "name": "register_date", "required": True, "width": "50%"},
                {"type": "text", "label": "患者姓名", "name": "patient_name", "required": True, "width": "50%"},
                {"type": "select", "label": "性别", "name": "gender", "required": True, "width": "50%", "options": ["男", "女"]},
                {"type": "number", "label": "年龄", "name": "age", "width": "50%"},
                {"type": "text", "label": "身份证号", "name": "id_card", "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "phone", "required": True, "width": "50%"},
                {"type": "select", "label": "挂号类型", "name": "register_type", "required": True, "width": "50%", "options": ["普通门诊", "专家门诊", "急诊", "特需门诊"]},
                {"type": "select", "label": "科室", "name": "department", "required": True, "width": "50%", "options": ["内科", "外科", "妇产科", "儿科", "骨科", "眼科", "耳鼻喉科", "口腔科", "皮肤科", "中医科"]},
                {"type": "text", "label": "医生", "name": "doctor", "width": "50%"},
                {"type": "textarea", "label": "主诉", "name": "chief_complaint", "required": True, "width": "100%"},
                {"type": "textarea", "label": "现病史", "name": "present_illness", "width": "100%"},
                {"type": "textarea", "label": "既往史", "name": "past_history", "width": "100%"},
                {"type": "money", "label": "挂号费", "name": "register_fee", "width": "50%"},
                {"type": "select", "label": "支付方式", "name": "payment_method", "width": "50%", "options": ["现金", "医保卡", "支付宝", "微信", "银行卡"]},
                {"type": "switch", "label": "是否初诊", "name": "is_first_visit", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "病历记录表",
        "code": "medical_record",
        "category": "general",
        "description": "患者病历信息记录",
        "modules": [{
            "name": "main",
            "label": "病历信息",
            "fields": [
                {"type": "text", "label": "病历号", "name": "record_no", "required": True, "width": "50%"},
                {"type": "text", "label": "患者姓名", "name": "patient_name", "required": True, "width": "50%"},
                {"type": "select", "label": "性别", "name": "gender", "width": "50%", "options": ["男", "女"]},
                {"type": "number", "label": "年龄", "name": "age", "width": "50%"},
                {"type": "date", "label": "就诊日期", "name": "visit_date", "required": True, "width": "50%"},
                {"type": "select", "label": "科室", "name": "department", "required": True, "width": "50%"},
                {"type": "text", "label": "主治医生", "name": "doctor", "required": True, "width": "50%"},
                {"type": "heading", "label": "病情描述", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "主诉", "name": "chief_complaint", "required": True, "width": "100%"},
                {"type": "textarea", "label": "现病史", "name": "present_illness", "width": "100%"},
                {"type": "textarea", "label": "既往史", "name": "past_history", "width": "100%"},
                {"type": "textarea", "label": "过敏史", "name": "allergy_history", "width": "100%"},
                {"type": "heading", "label": "检查诊断", "name": "h2", "width": "100%"},
                {"type": "textarea", "label": "体格检查", "name": "physical_exam", "width": "100%"},
                {"type": "textarea", "label": "辅助检查", "name": "auxiliary_exam", "width": "100%"},
                {"type": "textarea", "label": "初步诊断", "name": "diagnosis", "required": True, "width": "100%"},
                {"type": "heading", "label": "治疗方案", "name": "h3", "width": "100%"},
                {"type": "textarea", "label": "治疗建议", "name": "treatment", "width": "100%"},
                {"type": "textarea", "label": "处方药品", "name": "prescription", "width": "100%"},
                {"type": "textarea", "label": "医嘱", "name": "doctor_advice", "width": "100%"},
                {"type": "date", "label": "复诊日期", "name": "followup_date", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "药品入库单",
        "code": "drug_storage",
        "category": "inventory",
        "description": "药品采购入库登记",
        "modules": [{
            "name": "main",
            "label": "入库信息",
            "fields": [
                {"type": "text", "label": "入库单号", "name": "storage_no", "width": "50%"},
                {"type": "date", "label": "入库日期", "name": "storage_date", "required": True, "width": "50%"},
                {"type": "text", "label": "药品名称", "name": "drug_name", "required": True, "width": "50%"},
                {"type": "text", "label": "药品编码", "name": "drug_code", "width": "50%"},
                {"type": "text", "label": "规格", "name": "specification", "width": "50%"},
                {"type": "text", "label": "生产厂家", "name": "manufacturer", "width": "50%"},
                {"type": "text", "label": "批准文号", "name": "approval_no", "width": "50%"},
                {"type": "date", "label": "生产日期", "name": "production_date", "width": "50%"},
                {"type": "date", "label": "有效期至", "name": "expiry_date", "required": True, "width": "50%"},
                {"type": "number", "label": "入库数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "text", "label": "单位", "name": "unit", "width": "50%", "options": ["盒", "瓶", "支", "袋", "片"]},
                {"type": "money", "label": "单价", "name": "unit_price", "width": "50%"},
                {"type": "money", "label": "总价", "name": "total_price", "width": "50%"},
                {"type": "text", "label": "供应商", "name": "supplier", "width": "50%"},
                {"type": "text", "label": "入库人", "name": "operator", "required": True, "width": "50%"},
                {"type": "select", "label": "存放位置", "name": "storage_location", "width": "50%", "options": ["常温库", "阴凉库", "冷藏库", "特殊药品库"]},
                {"type": "textarea", "label": "备注", "name": "remark", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 通用业务 =====
    {
        "name": "来访登记表",
        "code": "visitor_register",
        "category": "general",
        "description": "外来人员来访登记",
        "modules": [{
            "name": "main",
            "label": "来访信息",
            "fields": [
                {"type": "text", "label": "来访编号", "name": "visit_no", "width": "50%"},
                {"type": "datetime", "label": "来访时间", "name": "visit_time", "required": True, "width": "50%"},
                {"type": "text", "label": "来访人姓名", "name": "visitor_name", "required": True, "width": "50%"},
                {"type": "select", "label": "性别", "name": "gender", "width": "50%", "options": ["男", "女"]},
                {"type": "text", "label": "身份证号", "name": "id_card", "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "phone", "width": "50%"},
                {"type": "text", "label": "来访单位", "name": "visitor_org", "width": "50%"},
                {"type": "text", "label": "被访人", "name": "visited_person", "required": True, "width": "50%"},
                {"type": "select", "label": "被访部门", "name": "visited_dept", "width": "50%"},
                {"type": "textarea", "label": "来访事由", "name": "visit_purpose", "required": True, "width": "100%"},
                {"type": "number", "label": "来访人数", "name": "visitor_count", "width": "50%"},
                {"type": "switch", "label": "是否携带物品", "name": "has_items", "width": "50%"},
                {"type": "textarea", "label": "携带物品", "name": "items", "width": "100%"},
                {"type": "datetime", "label": "离开时间", "name": "leave_time", "width": "50%"},
                {"type": "text", "label": "值班人员", "name": "duty_person", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "物品借用单",
        "code": "item_borrow",
        "category": "general",
        "description": "办公物品借用登记",
        "modules": [{
            "name": "main",
            "label": "借用信息",
            "fields": [
                {"type": "text", "label": "借用单号", "name": "borrow_no", "width": "50%"},
                {"type": "date", "label": "借用日期", "name": "borrow_date", "required": True, "width": "50%"},
                {"type": "text", "label": "借用人", "name": "borrower", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "dept", "width": "50%"},
                {"type": "text", "label": "物品名称", "name": "item_name", "required": True, "width": "50%"},
                {"type": "text", "label": "物品编号", "name": "item_no", "width": "50%"},
                {"type": "select", "label": "物品类别", "name": "item_category", "width": "50%", "options": ["电子设备", "办公用品", "工具", "其他"]},
                {"type": "number", "label": "借用数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "date", "label": "预计归还日期", "name": "expected_return", "required": True, "width": "50%"},
                {"type": "textarea", "label": "借用事由", "name": "reason", "required": True, "width": "100%"},
                {"type": "heading", "label": "归还信息", "name": "h1", "width": "100%"},
                {"type": "date", "label": "实际归还日期", "name": "actual_return", "width": "50%"},
                {"type": "select", "label": "物品状态", "name": "item_status", "width": "50%", "options": ["完好", "损坏", "丢失"]},
                {"type": "text", "label": "保管人", "name": "keeper", "width": "50%"}
            ]
        }],
        "is_published": True
    }
]


# 更多工作流
INDUSTRY_WORKFLOWS = [
    {
        "name": "生产任务下达流程",
        "code": "production_task_flow",
        "description": "生产计划下达和执行跟踪",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "plan", "type": "task", "name": "制定计划", "x": 300, "y": 100},
                {"id": "approve", "type": "task", "name": "计划审批", "x": 500, "y": 100},
                {"id": "dispatch", "type": "task", "name": "任务下达", "x": 700, "y": 100},
                {"id": "execute", "type": "task", "name": "生产执行", "x": 900, "y": 100},
                {"id": "inspect", "type": "task", "name": "质量检验", "x": 900, "y": 300},
                {"id": "end", "type": "end", "name": "结束", "x": 1100, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "plan"},
                {"id": "e2", "source": "plan", "target": "approve"},
                {"id": "e3", "source": "approve", "target": "dispatch", "condition": "approved"},
                {"id": "e4", "source": "dispatch", "target": "execute"},
                {"id": "e5", "source": "execute", "target": "inspect"},
                {"id": "e6", "source": "inspect", "target": "end", "condition": "qualified"}
            ]
        },
        "is_published": True
    },
    {
        "name": "学生入学流程",
        "code": "student_enrollment_flow",
        "description": "新生入学注册流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "register", "type": "task", "name": "报名登记", "x": 300, "y": 100},
                {"id": "verify", "type": "task", "name": "资料审核", "x": 500, "y": 100},
                {"id": "exam", "type": "task", "name": "入学考试", "x": 500, "y": 300},
                {"id": "admit", "type": "task", "name": "录取通知", "x": 700, "y": 100},
                {"id": "enroll", "type": "task", "name": "正式注册", "x": 900, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1100, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "register"},
                {"id": "e2", "source": "register", "target": "verify"},
                {"id": "e3", "source": "verify", "target": "exam"},
                {"id": "e4", "source": "exam", "target": "admit", "condition": "passed"},
                {"id": "e5", "source": "admit", "target": "enroll"},
                {"id": "e6", "source": "enroll", "target": "end"}
            ]
        },
        "is_published": True
    },
    {
        "name": "患者就诊流程",
        "code": "patient_visit_flow",
        "description": "门诊患者就诊流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "register", "type": "task", "name": "挂号", "x": 300, "y": 100},
                {"id": "triage", "type": "task", "name": "分诊", "x": 500, "y": 100},
                {"id": "consult", "type": "task", "name": "医生问诊", "x": 700, "y": 100},
                {"id": "exam", "type": "task", "name": "检查检验", "x": 700, "y": 300},
                {"id": "diagnosis", "type": "task", "name": "诊断开方", "x": 900, "y": 100},
                {"id": "pharmacy", "type": "task", "name": "取药", "x": 1100, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1300, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "register"},
                {"id": "e2", "source": "register", "target": "triage"},
                {"id": "e3", "source": "triage", "target": "consult"},
                {"id": "e4", "source": "consult", "target": "exam", "condition": "need_exam"},
                {"id": "e5", "source": "exam", "target": "diagnosis"},
                {"id": "e6", "source": "consult", "target": "diagnosis", "condition": "no_exam"},
                {"id": "e7", "source": "diagnosis", "target": "pharmacy"},
                {"id": "e8", "source": "pharmacy", "target": "end"}
            ]
        },
        "is_published": True
    }
]


async def init_industry_templates():
    async with AsyncSessionLocal() as db:
        print(f"Start importing {len(INDUSTRY_TEMPLATES)} industry templates...")
        
        for template_data in INDUSTRY_TEMPLATES:
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


async def init_industry_workflows():
    async with AsyncSessionLocal() as db:
        print(f"\nStart importing {len(INDUSTRY_WORKFLOWS)} industry workflows...")
        
        for workflow_data in INDUSTRY_WORKFLOWS:
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
    print("=" * 60)
    print("Kflower Industry Templates and Workflows Import Tool")
    print("=" * 60)
    
    try:
        await init_industry_templates()
        await init_industry_workflows()
        print("\n" + "=" * 60)
        print("Import completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
