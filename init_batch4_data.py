# -*- coding: utf-8 -*-
"""
生成第四批经典模板 - 更多行业专用模板
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

# 第四批模板
BATCH4_TEMPLATES = [
    # ===== IT/互联网 =====
    {
        "name": "Bug缺陷报告",
        "code": "bug_report",
        "category": "project",
        "description": "软件缺陷提交和跟踪",
        "modules": [{
            "name": "main",
            "label": "缺陷信息",
            "fields": [
                {"type": "text", "label": "缺陷标题", "name": "title", "required": True, "width": "100%"},
                {"type": "select", "label": "严重程度", "name": "severity", "required": True, "width": "50%", "options": ["致命", "严重", "一般", "轻微", "建议"]},
                {"type": "select", "label": "优先级", "name": "priority", "required": True, "width": "50%", "options": ["P0-紧急", "P1-高", "P2-中", "P3-低"]},
                {"type": "select", "label": "缺陷类型", "name": "bug_type", "width": "50%", "options": ["功能缺陷", "界面缺陷", "性能问题", "安全漏洞", "兼容性问题", "其他"]},
                {"type": "select", "label": "状态", "name": "status", "width": "50%", "options": ["新建", "已确认", "已分配", "已修复", "已验证", "已关闭", "重新打开"]},
                {"type": "text", "label": "所属模块", "name": "module", "width": "50%"},
                {"type": "text", "label": "发现版本", "name": "found_version", "width": "50%"},
                {"type": "text", "label": "修复版本", "name": "fixed_version", "width": "50%"},
                {"type": "text", "label": "指派给", "name": "assignee", "width": "50%"},
                {"type": "text", "label": "报告人", "name": "reporter", "width": "50%"},
                {"type": "heading", "label": "缺陷描述", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "复现步骤", "name": "steps", "required": True, "width": "100%"},
                {"type": "textarea", "label": "期望结果", "name": "expected", "required": True, "width": "100%"},
                {"type": "textarea", "label": "实际结果", "name": "actual", "required": True, "width": "100%"},
                {"type": "textarea", "label": "环境信息", "name": "environment", "width": "100%"},
                {"type": "upload", "label": "附件截图", "name": "attachments", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "需求变更申请单",
        "code": "requirement_change",
        "category": "project",
        "description": "需求变更申请和审批",
        "modules": [{
            "name": "main",
            "label": "变更信息",
            "fields": [
                {"type": "text", "label": "变更单号", "name": "change_no", "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "apply_date", "required": True, "width": "50%"},
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "text", "label": "所属项目", "name": "project", "required": True, "width": "50%"},
                {"type": "text", "label": "关联需求", "name": "related_requirement", "width": "50%"},
                {"type": "select", "label": "变更类型", "name": "change_type", "required": True, "width": "50%", "options": ["新增需求", "需求修改", "需求删除", "需求延期"]},
                {"type": "select", "label": "变更原因", "name": "change_reason", "width": "50%", "options": ["业务变更", "技术调整", "用户反馈", "法规要求", "其他"]},
                {"type": "select", "label": "紧急程度", "name": "urgency", "width": "50%", "options": ["紧急", "一般", "低"]},
                {"type": "textarea", "label": "变更内容描述", "name": "change_description", "required": True, "width": "100%"},
                {"type": "textarea", "label": "变更原因说明", "name": "reason_description", "width": "100%"},
                {"type": "textarea", "label": "影响范围评估", "name": "impact_analysis", "width": "100%"},
                {"type": "heading", "label": "评估信息", "name": "h1", "width": "100%"},
                {"type": "number", "label": "预估工作量(人天)", "name": "workload", "width": "50%"},
                {"type": "date", "label": "预计完成日期", "name": "expected_date", "width": "50%"},
                {"type": "heading", "label": "审批意见", "name": "h2", "width": "100%"},
                {"type": "textarea", "label": "项目经理意见", "name": "pm_opinion", "width": "100%"},
                {"type": "textarea", "label": "技术负责人意见", "name": "tech_opinion", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "服务器资源申请单",
        "code": "server_request",
        "category": "project",
        "description": "IT服务器资源申请",
        "modules": [{
            "name": "main",
            "label": "申请信息",
            "fields": [
                {"type": "text", "label": "申请人", "name": "applicant", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "date", "label": "申请日期", "name": "apply_date", "required": True, "width": "50%"},
                {"type": "text", "label": "项目名称", "name": "project_name", "required": True, "width": "50%"},
                {"type": "select", "label": "资源类型", "name": "resource_type", "required": True, "width": "50%", "options": ["云服务器", "物理服务器", "数据库", "存储", "带宽", "域名", "SSL证书"]},
                {"type": "select", "label": "环境", "name": "environment", "required": True, "width": "50%", "options": ["开发环境", "测试环境", "预发布环境", "生产环境"]},
                {"type": "heading", "label": "配置要求", "name": "h1", "width": "100%"},
                {"type": "select", "label": "CPU核心数", "name": "cpu_cores", "width": "50%", "options": ["2核", "4核", "8核", "16核", "32核"]},
                {"type": "select", "label": "内存大小", "name": "memory", "width": "50%", "options": ["2GB", "4GB", "8GB", "16GB", "32GB", "64GB"]},
                {"type": "select", "label": "硬盘大小", "name": "storage", "width": "50%", "options": ["50GB", "100GB", "200GB", "500GB", "1TB", "2TB"]},
                {"type": "select", "label": "操作系统", "name": "os", "width": "50%", "options": ["CentOS 7", "CentOS 8", "Ubuntu 20.04", "Ubuntu 22.04", "Windows Server 2019", "Windows Server 2022"]},
                {"type": "number", "label": "数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "daterange", "label": "使用期限", "name": "usage_period", "required": True, "width": "50%"},
                {"type": "textarea", "label": "用途说明", "name": "purpose", "required": True, "width": "100%"},
                {"type": "textarea", "label": "网络要求", "name": "network_requirements", "width": "100%"},
                {"type": "heading", "label": "安全要求", "name": "h2", "width": "100%"},
                {"type": "switch", "label": "需要外网访问", "name": "need_internet", "width": "50%"},
                {"type": "switch", "label": "需要SSL证书", "name": "need_ssl", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 零售/电商 =====
    {
        "name": "商品入库单",
        "code": "product_inbound",
        "category": "inventory",
        "description": "商品入库登记",
        "modules": [{
            "name": "main",
            "label": "入库信息",
            "fields": [
                {"type": "text", "label": "入库单号", "name": "inbound_no", "width": "50%"},
                {"type": "date", "label": "入库日期", "name": "inbound_date", "required": True, "width": "50%"},
                {"type": "select", "label": "入库类型", "name": "inbound_type", "required": True, "width": "50%", "options": ["采购入库", "退货入库", "调拨入库", "其他入库"]},
                {"type": "text", "label": "供应商", "name": "supplier", "width": "50%"},
                {"type": "text", "label": "采购单号", "name": "purchase_no", "width": "50%"},
                {"type": "text", "label": "仓库", "name": "warehouse", "required": True, "width": "50%"},
                {"type": "heading", "label": "商品信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "商品编码", "name": "product_code", "required": True, "width": "50%"},
                {"type": "text", "label": "商品名称", "name": "product_name", "required": True, "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "text", "label": "条形码", "name": "barcode", "width": "50%"},
                {"type": "number", "label": "入库数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "text", "label": "单位", "name": "unit", "width": "50%"},
                {"type": "money", "label": "单价", "name": "unit_price", "width": "50%"},
                {"type": "money", "label": "总金额", "name": "total_amount", "width": "50%"},
                {"type": "text", "label": "批次号", "name": "batch_no", "width": "50%"},
                {"type": "date", "label": "生产日期", "name": "production_date", "width": "50%"},
                {"type": "date", "label": "有效期至", "name": "expiry_date", "width": "50%"},
                {"type": "heading", "label": "确认信息", "name": "h2", "width": "100%"},
                {"type": "text", "label": "验收人", "name": "inspector", "width": "50%"},
                {"type": "text", "label": "入库人", "name": "operator", "width": "50%"},
                {"type": "textarea", "label": "备注", "name": "remark", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "商品出库单",
        "code": "product_outbound",
        "category": "inventory",
        "description": "商品出库登记",
        "modules": [{
            "name": "main",
            "label": "出库信息",
            "fields": [
                {"type": "text", "label": "出库单号", "name": "outbound_no", "width": "50%"},
                {"type": "date", "label": "出库日期", "name": "outbound_date", "required": True, "width": "50%"},
                {"type": "select", "label": "出库类型", "name": "outbound_type", "required": True, "width": "50%", "options": ["销售出库", "调拨出库", "报损出库", "退货出库", "其他出库"]},
                {"type": "text", "label": "销售单号", "name": "sales_no", "width": "50%"},
                {"type": "text", "label": "仓库", "name": "warehouse", "required": True, "width": "50%"},
                {"type": "heading", "label": "商品信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "商品编码", "name": "product_code", "required": True, "width": "50%"},
                {"type": "text", "label": "商品名称", "name": "product_name", "required": True, "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "number", "label": "出库数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "text", "label": "单位", "name": "unit", "width": "50%"},
                {"type": "money", "label": "单价", "name": "unit_price", "width": "50%"},
                {"type": "money", "label": "总金额", "name": "total_amount", "width": "50%"},
                {"type": "text", "label": "批次号", "name": "batch_no", "width": "50%"},
                {"type": "heading", "label": "客户信息", "name": "h2", "width": "100%"},
                {"type": "text", "label": "客户名称", "name": "customer_name", "width": "50%"},
                {"type": "text", "label": "收货人", "name": "receiver", "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "phone", "width": "50%"},
                {"type": "textarea", "label": "收货地址", "name": "address", "width": "100%"},
                {"type": "heading", "label": "确认信息", "name": "h3", "width": "100%"},
                {"type": "text", "label": "拣货人", "name": "picker", "width": "50%"},
                {"type": "text", "label": "复核人", "name": "checker", "width": "50%"},
                {"type": "text", "label": "出库人", "name": "operator", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "库存盘点表",
        "code": "inventory_check",
        "category": "inventory",
        "description": "库存盘点记录",
        "modules": [{
            "name": "main",
            "label": "盘点信息",
            "fields": [
                {"type": "text", "label": "盘点单号", "name": "check_no", "width": "50%"},
                {"type": "date", "label": "盘点日期", "name": "check_date", "required": True, "width": "50%"},
                {"type": "text", "label": "仓库", "name": "warehouse", "required": True, "width": "50%"},
                {"type": "select", "label": "盘点类型", "name": "check_type", "required": True, "width": "50%", "options": ["全盘", "抽盘", "循环盘点"]},
                {"type": "heading", "label": "商品信息", "name": "h1", "width": "100%"},
                {"type": "text", "label": "商品编码", "name": "product_code", "required": True, "width": "50%"},
                {"type": "text", "label": "商品名称", "name": "product_name", "required": True, "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "text", "label": "批次号", "name": "batch_no", "width": "50%"},
                {"type": "text", "label": "库位", "name": "location", "width": "50%"},
                {"type": "heading", "label": "盘点数量", "name": "h2", "width": "100%"},
                {"type": "number", "label": "系统库存", "name": "system_quantity", "required": True, "width": "50%"},
                {"type": "number", "label": "实盘数量", "name": "actual_quantity", "required": True, "width": "50%"},
                {"type": "number", "label": "盘盈数量", "name": "surplus_quantity", "width": "50%"},
                {"type": "number", "label": "盘亏数量", "name": "loss_quantity", "width": "50%"},
                {"type": "money", "label": "盘盈金额", "name": "surplus_amount", "width": "50%"},
                {"type": "money", "label": "盘亏金额", "name": "loss_amount", "width": "50%"},
                {"type": "heading", "label": "确认信息", "name": "h3", "width": "100%"},
                {"type": "textarea", "label": "差异原因", "name": "difference_reason", "width": "100%"},
                {"type": "text", "label": "盘点人", "name": "checker", "required": True, "width": "50%"},
                {"type": "text", "label": "监盘人", "name": "supervisor", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 物流运输 =====
    {
        "name": "发货单",
        "code": "delivery_order",
        "category": "inventory",
        "description": "商品发货登记",
        "modules": [{
            "name": "main",
            "label": "发货信息",
            "fields": [
                {"type": "text", "label": "发货单号", "name": "delivery_no", "width": "50%"},
                {"type": "date", "label": "发货日期", "name": "delivery_date", "required": True, "width": "50%"},
                {"type": "text", "label": "销售订单号", "name": "sales_order_no", "width": "50%"},
                {"type": "text", "label": "客户名称", "name": "customer_name", "required": True, "width": "50%"},
                {"type": "text", "label": "联系人", "name": "contact_person", "width": "50%"},
                {"type": "phone", "label": "联系电话", "name": "phone", "required": True, "width": "50%"},
                {"type": "textarea", "label": "收货地址", "name": "address", "required": True, "width": "100%"},
                {"type": "heading", "label": "货物信息", "name": "h1", "width": "100%"},
                {"type": "number", "label": "总件数", "name": "total_packages", "required": True, "width": "50%"},
                {"type": "number", "label": "总重量(kg)", "name": "total_weight", "width": "50%"},
                {"type": "number", "label": "总体积(m³)", "name": "total_volume", "width": "50%"},
                {"type": "heading", "label": "物流信息", "name": "h2", "width": "100%"},
                {"type": "select", "label": "发货方式", "name": "delivery_method", "required": True, "width": "50%", "options": ["快递", "物流", "自提", "送货上门"]},
                {"type": "text", "label": "物流公司", "name": "logistics_company", "width": "50%"},
                {"type": "text", "label": "物流单号", "name": "tracking_no", "width": "50%"},
                {"type": "money", "label": "运费", "name": "freight", "width": "50%"},
                {"type": "select", "label": "运费支付", "name": "freight_payment", "width": "50%", "options": ["寄付", "到付", "月结"]},
                {"type": "heading", "label": "确认信息", "name": "h3", "width": "100%"},
                {"type": "text", "label": "发货人", "name": "sender", "width": "50%"},
                {"type": "text", "label": "制单人", "name": "creator", "width": "50%"},
                {"type": "textarea", "label": "备注", "name": "remark", "width": "100%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 行政后勤 =====
    {
        "name": "办公用品领用单",
        "code": "office_supplies",
        "category": "general",
        "description": "办公用品领用登记",
        "modules": [{
            "name": "main",
            "label": "领用信息",
            "fields": [
                {"type": "text", "label": "领用单号", "name": "request_no", "width": "50%"},
                {"type": "date", "label": "领用日期", "name": "request_date", "required": True, "width": "50%"},
                {"type": "text", "label": "领用人", "name": "requester", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "heading", "label": "物品明细", "name": "h1", "width": "100%"},
                {"type": "text", "label": "物品名称", "name": "item_name", "required": True, "width": "50%"},
                {"type": "text", "label": "规格型号", "name": "specification", "width": "50%"},
                {"type": "number", "label": "数量", "name": "quantity", "required": True, "width": "50%"},
                {"type": "text", "label": "单位", "name": "unit", "width": "50%"},
                {"type": "textarea", "label": "领用事由", "name": "reason", "required": True, "width": "100%"},
                {"type": "heading", "label": "审批信息", "name": "h2", "width": "100%"},
                {"type": "text", "label": "部门负责人", "name": "dept_manager", "width": "50%"},
                {"type": "text", "label": "行政审核", "name": "admin_approval", "width": "50%"},
                {"type": "text", "label": "发放人", "name": "issuer", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    {
        "name": "会议室预约申请",
        "code": "meeting_room_booking",
        "category": "general",
        "description": "会议室预约登记",
        "modules": [{
            "name": "main",
            "label": "预约信息",
            "fields": [
                {"type": "text", "label": "预约人", "name": "booker", "required": True, "width": "50%"},
                {"type": "select", "label": "部门", "name": "department", "required": True, "width": "50%"},
                {"type": "date", "label": "会议日期", "name": "meeting_date", "required": True, "width": "50%"},
                {"type": "time", "label": "开始时间", "name": "start_time", "required": True, "width": "50%"},
                {"type": "time", "label": "结束时间", "name": "end_time", "required": True, "width": "50%"},
                {"type": "select", "label": "会议室", "name": "meeting_room", "required": True, "width": "50%", "options": ["会议室A(10人)", "会议室B(20人)", "大会议室(50人)", "多功能厅(100人)"]},
                {"type": "text", "label": "会议主题", "name": "subject", "required": True, "width": "100%"},
                {"type": "number", "label": "参会人数", "name": "attendee_count", "required": True, "width": "50%"},
                {"type": "textarea", "label": "参会人员", "name": "attendees", "width": "100%"},
                {"type": "textarea", "label": "会议内容", "name": "content", "width": "100%"},
                {"type": "heading", "label": "设备需求", "name": "h1", "width": "100%"},
                {"type": "checkbox", "label": "所需设备", "name": "equipment", "options": ["投影仪", "电脑", "白板", "麦克风", "视频会议设备", "茶水服务"], "width": "100%"},
                {"type": "switch", "label": "需要视频会议", "name": "need_video", "width": "50%"}
            ]
        }],
        "is_published": True
    },
    
    # ===== 安全管理 =====
    {
        "name": "安全事故报告",
        "code": "safety_incident",
        "category": "general",
        "description": "安全事故报告和记录",
        "modules": [{
            "name": "main",
            "label": "事故信息",
            "fields": [
                {"type": "text", "label": "报告编号", "name": "report_no", "width": "50%"},
                {"type": "datetime", "label": "事故发生时间", "name": "incident_time", "required": True, "width": "50%"},
                {"type": "text", "label": "事故地点", "name": "location", "required": True, "width": "50%"},
                {"type": "select", "label": "事故类型", "name": "incident_type", "required": True, "width": "50%", "options": ["人身伤害", "财产损失", "火灾事故", "交通事故", "设备事故", "其他"]},
                {"type": "select", "label": "事故等级", "name": "incident_level", "required": True, "width": "50%", "options": ["一般事故", "较大事故", "重大事故", "特别重大事故"]},
                {"type": "text", "label": "报告人", "name": "reporter", "required": True, "width": "50%"},
                {"type": "datetime", "label": "报告时间", "name": "report_time", "required": True, "width": "50%"},
                {"type": "heading", "label": "事故详情", "name": "h1", "width": "100%"},
                {"type": "textarea", "label": "事故经过", "name": "incident_description", "required": True, "width": "100%"},
                {"type": "textarea", "label": "人员伤亡情况", "name": "casualty_info", "width": "100%"},
                {"type": "textarea", "label": "财产损失情况", "name": "property_loss", "width": "100%"},
                {"type": "textarea", "label": "初步原因分析", "name": "initial_cause", "width": "100%"},
                {"type": "textarea", "label": "已采取的措施", "name": "measures_taken", "width": "100%"},
                {"type": "heading", "label": "附件", "name": "h2", "width": "100%"},
                {"type": "image", "label": "现场照片", "name": "photos", "width": "100%"},
                {"type": "upload", "label": "相关文件", "name": "documents", "width": "100%"}
            ]
        }],
        "is_published": True
    }
]


# 第四批工作流
BATCH4_WORKFLOWS = [
    {
        "name": "Bug处理流程",
        "code": "bug_process_flow",
        "description": "软件缺陷从提交到关闭的完整流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "submit", "type": "task", "name": "提交缺陷", "x": 300, "y": 100},
                {"id": "triage", "type": "task", "name": "缺陷分级", "x": 500, "y": 100},
                {"id": "assign", "type": "task", "name": "分配开发", "x": 700, "y": 100},
                {"id": "fix", "type": "task", "name": "修复缺陷", "x": 900, "y": 100},
                {"id": "verify", "type": "task", "name": "验证修复", "x": 900, "y": 300},
                {"id": "close", "type": "task", "name": "关闭缺陷", "x": 1100, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1300, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "submit"},
                {"id": "e2", "source": "submit", "target": "triage"},
                {"id": "e3", "source": "triage", "target": "assign"},
                {"id": "e4", "source": "assign", "target": "fix"},
                {"id": "e5", "source": "fix", "target": "verify"},
                {"id": "e6", "source": "verify", "target": "close", "condition": "passed"},
                {"id": "e7", "source": "verify", "target": "fix", "condition": "failed"},
                {"id": "e8", "source": "close", "target": "end"}
            ]
        },
        "is_published": True
    },
    {
        "name": "库存盘点流程",
        "code": "inventory_check_flow",
        "description": "库存盘点从准备到完成的流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "plan", "type": "task", "name": "制定盘点计划", "x": 300, "y": 100},
                {"id": "prepare", "type": "task", "name": "盘点准备", "x": 500, "y": 100},
                {"id": "count", "type": "task", "name": "实地盘点", "x": 700, "y": 100},
                {"id": "compare", "type": "task", "name": "差异核对", "x": 900, "y": 100},
                {"id": "adjust", "type": "task", "name": "账务调整", "x": 900, "y": 300},
                {"id": "report", "type": "task", "name": "生成报告", "x": 1100, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1300, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "plan"},
                {"id": "e2", "source": "plan", "target": "prepare"},
                {"id": "e3", "source": "prepare", "target": "count"},
                {"id": "e4", "source": "count", "target": "compare"},
                {"id": "e5", "source": "compare", "target": "adjust", "condition": "has_difference"},
                {"id": "e6", "source": "compare", "target": "report", "condition": "no_difference"},
                {"id": "e7", "source": "adjust", "target": "report"},
                {"id": "e8", "source": "report", "target": "end"}
            ]
        },
        "is_published": True
    },
    {
        "name": "会议室预约审批流程",
        "code": "meeting_room_flow",
        "description": "会议室预约审批流程",
        "definition": {
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 100},
                {"id": "apply", "type": "task", "name": "提交预约", "x": 300, "y": 100},
                {"id": "check", "type": "task", "name": "检查可用性", "x": 500, "y": 100},
                {"id": "approve", "type": "task", "name": "审批", "x": 700, "y": 100},
                {"id": "confirm", "type": "task", "name": "确认预约", "x": 900, "y": 100},
                {"id": "end", "type": "end", "name": "结束", "x": 1100, "y": 100}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "check"},
                {"id": "e3", "source": "check", "target": "approve", "condition": "available"},
                {"id": "e4", "source": "check", "target": "apply", "condition": "unavailable"},
                {"id": "e5", "source": "approve", "target": "confirm", "condition": "approved"},
                {"id": "e6", "source": "confirm", "target": "end"}
            ]
        },
        "is_published": True
    }
]


async def init_batch4_templates():
    async with AsyncSessionLocal() as db:
        print(f"Start importing {len(BATCH4_TEMPLATES)} templates (Batch 4)...")
        
        for template_data in BATCH4_TEMPLATES:
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
            print(f"  [OK] Created: {template_data['name']}")
        
        await db.commit()
        print("Templates import completed!")


async def init_batch4_workflows():
    async with AsyncSessionLocal() as db:
        print(f"\nStart importing {len(BATCH4_WORKFLOWS)} workflows (Batch 4)...")
        
        for workflow_data in BATCH4_WORKFLOWS:
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
            print(f"  [OK] Created: {workflow_data['name']}")
        
        await db.commit()
        print("Workflows import completed!")


async def main():
    print("=" * 60)
    print("Kflower Templates and Workflows Import Tool - Batch 4")
    print("=" * 60)
    
    try:
        await init_batch4_templates()
        await init_batch4_workflows()
        print("\n" + "=" * 60)
        print("Import completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
