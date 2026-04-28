"""
数据模型 → Kflower模板 转换引擎
将数据模型定义反向生成为Kflower模板格式，与手动创建的模板完全兼容
"""
from typing import List, Dict, Any, Optional
from app.models.data_model import DataModel, DataModelField, DataModelRelation


class ModelToTemplateConverter:
    """数据模型 → Kflower模板 转换器"""

    # 数据库类型 → UI控件 映射
    DB_TYPE_TO_UI: Dict[str, str] = {
        # 数值类
        "INTEGER": "number",
        "INT": "number",
        "BIGINT": "number",
        "SMALLINT": "number",
        "TINYINT": "switch",
        "REAL": "number",
        "FLOAT": "number",
        "DOUBLE": "number",
        "DECIMAL": "number",
        "NUMERIC": "number",
        # 字符串类
        "VARCHAR": "text",
        "CHAR": "text",
        "TEXT": "text",
        "LONGTEXT": "text",
        "MEDIUMTEXT": "text",
        "CLOB": "text",
        # 日期类
        "DATE": "date",
        "DATETIME": "datetime",
        "TIMESTAMP": "datetime",
        "TIME": "text",
        # 布尔类
        "BOOLEAN": "switch",
        "BOOL": "switch",
        # 二进制
        "BLOB": "upload",
        "BINARY": "upload",
        # JSON
        "JSON": "subform",
        "JSONB": "subform",
    }

    # 字段名智能识别 → UI控件
    SMART_TYPE_MAP: Dict[str, str] = {
        "email": "text",
        "phone": "text",
        "mobile": "text",
        "url": "text",
        "website": "text",
        "password": "text",
        "avatar": "image",
        "image": "image",
        "photo": "image",
        "logo": "image",
        "icon": "image",
        "file": "upload",
        "attachment": "upload",
        "amount": "number",
        "price": "number",
        "money": "number",
        "salary": "number",
        "percent": "number",
        "ratio": "number",
        "status": "select",
        "type": "select",
        "category": "select",
        "level": "select",
        "gender": "radio",
        "sex": "radio",
        "color": "text",
        "remark": "text",
        "note": "text",
        "description": "text",
        "address": "text",
        "tags": "checkbox",
        "enabled": "switch",
        "is_vip": "switch",
        "is_active": "switch",
    }

    # 字段名 → 中文标签
    NAME_TO_LABEL: Dict[str, str] = {
        "id": "编号", "name": "名称", "title": "标题", "code": "编码",
        "phone": "电话", "mobile": "手机", "email": "邮箱", "address": "地址",
        "remark": "备注", "note": "备注", "description": "描述",
        "status": "状态", "type": "类型", "category": "分类", "level": "级别",
        "amount": "金额", "price": "价格", "total": "合计", "quantity": "数量",
        "count": "数量", "date": "日期", "time": "时间", "created_at": "创建时间",
        "updated_at": "更新时间", "created_by": "创建人", "updated_by": "更新人",
        "gender": "性别", "age": "年龄", "avatar": "头像", "logo": "Logo",
        "url": "网址", "website": "网站", "password": "密码",
        "customer": "客户", "supplier": "供应商", "order": "订单",
        "product": "产品", "department": "部门", "position": "职位",
        "salary": "薪资", "score": "分数", "weight": "重量",
        "height": "高度", "width": "宽度", "color": "颜色", "size": "尺寸",
        "enabled": "是否启用", "is_vip": "VIP", "is_active": "是否有效",
        "sort_order": "排序", "parent_id": "上级", "path": "路径",
        "company": "公司", "contact": "联系人", "source": "来源",
        "priority": "优先级", "deadline": "截止日期", "start_date": "开始日期",
        "end_date": "结束日期", "creator": "创建人", "assignee": "负责人",
        "progress": "进度", "budget": "预算", "cost": "成本",
    }

    def convert(self, model: DataModel, fields: List[DataModelField],
                relations: List[DataModelRelation] = None) -> dict:
        """将数据模型转换为 Kflower 模板格式（与 TemplateCreate 的 modules 结构完全兼容）"""

        # 构建字段列表
        module_fields = []
        sorted_fields = sorted(fields, key=lambda f: f.sort_order)

        for field in sorted_fields:
            # 自增主键不放入表单
            if field.is_primary_key and field.is_auto_increment:
                continue
            # 系统字段不放入表单
            if field.is_system and field.name in ('created_at', 'updated_at', 'created_by', 'updated_by'):
                continue

            field_dict = self._convert_field(field, relations)
            module_fields.append(field_dict)

        # 构建模板数据
        template_data = {
            "name": model.title or model.name,
            "code": f"dm_{model.id}",
            "description": model.description or f"从数据模型 '{model.name}' 生成",
            "category": "data_model",
            "config": {
                "source_type": "data_model",
                "data_model_id": model.id,
                "table_name": model.table_name or f"form_data_dm_{model.id}",
            },
            "modules": [
                {
                    "name": model.name,
                    "label": model.title or model.name,
                    "fields": module_fields
                }
            ]
        }

        return template_data

    def _convert_field(self, field: DataModelField,
                       relations: List[DataModelRelation] = None) -> dict:
        """转换单个字段"""

        # 确定UI控件类型
        ui_type = self._determine_ui_type(field)

        # 构建字段定义
        result: Dict[str, Any] = {
            "name": field.name,
            "type": ui_type,
            "label": field.title or self._auto_label(field.name),
            "required": field.is_required,
            "readonly": field.is_primary_key and not field.is_auto_increment,
            "hidden": False,
        }

        # 默认值
        if field.default_value is not None:
            result["defaultValue"] = field.default_value

        # 选项
        if field.options:
            opts = field.options if isinstance(field.options, list) else []
            result["options"] = [opt.get("label", opt.get("value", "")) for opt in opts]
            result["optionsText"] = "\n".join(opt.get("label", opt.get("value", "")) for opt in opts)

        # 长度限制
        if field.max_length:
            result["maxLength"] = field.max_length

        # 数值范围
        if field.min_value is not None:
            result["min"] = field.min_value
        if field.max_value is not None:
            result["max"] = field.max_value

        # 描述
        if field.description:
            result["description"] = field.description

        # 占位提示
        if field.placeholder:
            result["placeholder"] = field.placeholder

        # 宽度
        if field.width and field.width != "100%":
            result["width"] = field.width

        # 关联配置
        if field.relation_config and isinstance(field.relation_config, dict):
            rel = field.relation_config
            result["relation"] = {
                "target_template": rel.get("target_model_name", ""),
                "display_field": rel.get("display_field", "name"),
                "link_field": field.name,
            }
            if ui_type != "relation":
                result["type"] = "relation"

        return result

    def _determine_ui_type(self, field: DataModelField) -> str:
        """智能确定UI控件类型"""

        # 1. 已有UI类型
        if field.ui_type:
            return field.ui_type

        # 2. 关联字段
        if field.relation_config and isinstance(field.relation_config, dict) and field.relation_config.get("target_model_id"):
            return "relation"

        # 3. 字段名智能识别
        name_lower = field.name.lower()
        for pattern, ui_type in self.SMART_TYPE_MAP.items():
            if pattern in name_lower:
                return ui_type

        # 4. 按数据库类型映射
        db_type_upper = field.db_type.upper()
        base_type = db_type_upper.split('(')[0].strip()
        return self.DB_TYPE_TO_UI.get(base_type, "text")

    def _auto_label(self, field_name: str) -> str:
        """自动将字段名转为中文标签"""

        # 精确匹配
        if field_name in self.NAME_TO_LABEL:
            return self.NAME_TO_LABEL[field_name]

        # 去除常见后缀后再匹配
        suffix_map = {
            '_id': 'ID',
            '_name': '',
            '_code': '编码',
            '_type': '类型',
            '_at': '时间',
            '_by': '人',
            '_date': '日期',
            '_time': '时间',
        }
        for suffix, label_suffix in suffix_map.items():
            if field_name.endswith(suffix):
                base = field_name[:-len(suffix)]
                base_label = self.NAME_TO_LABEL.get(base)
                if base_label:
                    return f"{base_label}{label_suffix}" if label_suffix else base_label

        # 下划线转空格 + 首字母大写
        return field_name.replace('_', ' ').title()

    @staticmethod
    def db_type_to_sqlite(db_type: str, max_length: int = None) -> str:
        """将通用数据库类型映射为SQLite类型"""
        type_map = {
            "INTEGER": "INTEGER",
            "INT": "INTEGER",
            "BIGINT": "INTEGER",
            "SMALLINT": "INTEGER",
            "TINYINT": "INTEGER",
            "REAL": "REAL",
            "FLOAT": "REAL",
            "DOUBLE": "REAL",
            "DECIMAL": "REAL",
            "NUMERIC": "REAL",
            "VARCHAR": "TEXT",
            "CHAR": "TEXT",
            "TEXT": "TEXT",
            "LONGTEXT": "TEXT",
            "MEDIUMTEXT": "TEXT",
            "CLOB": "TEXT",
            "DATE": "TEXT",
            "DATETIME": "TEXT",
            "TIMESTAMP": "TEXT",
            "TIME": "TEXT",
            "BOOLEAN": "INTEGER",
            "BOOL": "INTEGER",
            "BLOB": "BLOB",
            "BINARY": "BLOB",
            "JSON": "TEXT",
            "JSONB": "TEXT",
        }
        base = db_type.upper().split('(')[0].strip()
        return type_map.get(base, "TEXT")
