# -*- coding: utf-8 -*-
"""
智能导入服务 - 从Excel/CSV/图片OCR解析生成表单字段
依赖: openpyxl, pandas, jieba, pytesseract, PIL, cv2
"""
import re
import json
import uuid
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pytesseract
from PIL import Image
import numpy as np

# Excel 支持
try:
    import openpyxl
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# jieba 分词
try:
    import jieba
    import jieba.analyse
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

# 中文同义词映射
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


# ============ 字段类型推断规则 ============
FIELD_TYPE_KEYWORDS = {
    'text': [
        '姓名', '名称', '公司', '地址', '备注', '说明', '描述', '标题', '主题',
        '职位', '岗位', '部门', '姓名', '联系人', '供应商', '客户', '品牌',
        '产品', '型号', '规格', '单位', '编码', '编号', '税号', '开户行',
        'reason', 'name', 'title', 'address', 'desc', 'note', 'remark'
    ],
    'number': [
        '数量', '金额', '价格', '单价', '总价', '折扣', '税率', '比率',
        '比例', '百分比', '面积', '体积', '重量', '长度', '高度',
        'qty', 'amount', 'price', 'rate', 'ratio', 'num', 'count'
    ],
    'phone': [
        '电话', '手机', '固话', '传真', '号码', 'tel', 'phone', 'mobile', 'fax'
    ],
    'email': [
        '邮箱', '邮件', 'email', 'mail'
    ],
    'date': [
        '日期', '时间', '时间', '生日', '到期', '有效期', '创建时间', '更新时间',
        '入职日期', '离职日期', 'date', 'time', 'birthday', 'expire'
    ],
    'select': [
        '类型', '分类', '状态', '等级', '方式', '渠道', '来源',
        'type', 'category', 'status', 'level', 'method', 'channel'
    ],
    'checkbox': [
        '选项', '多选', '爱好', '特长', '技能',
    ],
    'money': [
        '工资', '薪酬', '预算', '成本', '利润', '收入', '支出', '借款', 'salary', 'budget', 'cost'
    ],
    'url': [
        '网址', '链接', '网站', 'url', 'website', 'link'
    ]
}

# 表头关键词 → 字段名映射（自动生成英文字段名）
FIELD_NAME_MAP = {
    '姓名': 'name', '名称': 'name', '公司': 'company', '地址': 'address',
    '电话': 'phone', '手机': 'mobile', '固话': 'tel', '传真': 'fax',
    '邮箱': 'email', '邮件': 'email',
    '日期': 'date', '时间': 'time', '生日': 'birthday',
    '数量': 'quantity', '金额': 'amount', '价格': 'price', '单价': 'unit_price',
    '总价': 'total_price', '税率': 'tax_rate', '折扣': 'discount',
    '类型': 'type', '分类': 'category', '状态': 'status', '等级': 'level',
    '备注': 'remark', '说明': 'description', '描述': 'description',
    '编码': 'code', '编号': 'code', '序号': 'seq_no',
    '职位': 'position', '岗位': 'position', '部门': 'department',
    '联系人': 'contact', '供应商': 'supplier', '客户': 'customer',
    '产品': 'product', '型号': 'model', '规格': 'spec',
    '品牌': 'brand', '单位': 'unit',
    '税号': 'tax_no', '开户行': 'bank', '账号': 'account_no',
    '开始日期': 'start_date', '结束日期': 'end_date',
    '创建人': 'creator', '创建时间': 'create_time',
    '修改人': 'modifier', '修改时间': 'update_time',
    '审批人': 'approver', '审批时间': 'approve_time',
    '审批意见': 'opinion', '结果': 'result',
    '操作': 'action', '选择': 'option',
    '爱好': 'hobbies', '特长': 'skills', '技能': 'skills',
}


def chinese_to_pinyin(text: str) -> str:
    """简单的中文转拼音首字母 + 完整拼音"""
    if not text:
        return 'field'
    # 简单实现：用已有映射
    result = FIELD_NAME_MAP.get(text.strip(), '')
    if result:
        return result
    # 逐字符匹配
    pinyin = ''
    for char in text:
        for key, val in FIELD_NAME_MAP.items():
            if key.startswith(char):
                pinyin += val
                break
    if not pinyin:
        # 用jieba分词
        if JIEBA_AVAILABLE:
            words = jieba.cut(text)
            for w in words:
                if w.strip() and len(w) > 1:
                    mapped = FIELD_NAME_MAP.get(w, '')
                    if mapped:
                        pinyin += mapped
                        break
    if not pinyin:
        pinyin = text[:3]
    # 清理并转小写
    pinyin = re.sub(r'[^a-z0-9_]', '_', pinyin.lower())
    pinyin = re.sub(r'_+', '_', pinyin).strip('_')
    return pinyin or 'field'


def infer_field_type(header: str, values: List[Any] = None) -> str:
    """根据表头名称和数据内容推断字段类型"""
    header_lower = header.lower()
    header_clean = header.strip()

    # 关键词匹配
    for ftype, keywords in FIELD_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in header_clean or kw in header_lower:
                # 进一步检查是否为纯数字列
                if ftype == 'text' and values:
                    numeric_count = sum(1 for v in values[:10] if _is_numeric(str(v)))
                    if numeric_count > 7:
                        return 'number'
                return ftype

    # 数据内容分析
    if values:
        non_empty = [str(v).strip() for v in values if v is not None and str(v).strip()]
        if not non_empty:
            return 'text'

        # 数字检测
        numeric_count = sum(1 for v in non_empty[:20] if _is_numeric(v))
        if numeric_count > len(non_empty) * 0.7:
            return 'number'

        # 日期检测
        date_count = sum(1 for v in non_empty[:20] if _is_date(v))
        if date_count > len(non_empty) * 0.7:
            return 'date'

        # 邮箱检测
        email_count = sum(1 for v in non_empty if '@' in v and '.' in v)
        if email_count > len(non_empty) * 0.5:
            return 'email'

        # 电话检测
        phone_count = sum(1 for v in non_empty if _is_phone(v))
        if phone_count > len(non_empty) * 0.5:
            return 'phone'

        # 选项型（值种类少）
        unique_vals = set(non_empty[:50])
        if 1 < len(unique_vals) <= 10 and all(len(str(v)) < 20 for v in unique_vals):
            return 'select'

    return 'text'


def _is_numeric(s: str) -> bool:
    """判断是否为数字"""
    s = str(s).replace(',', '').replace(' ', '').replace('¥', '').replace('$', '').replace('%', '')
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_date(s: str) -> bool:
    """判断是否为日期"""
    s = str(s).strip()
    date_patterns = [
        r'^\d{4}-\d{1,2}-\d{1,2}',  # 2024-01-01
        r'^\d{4}/\d{1,2}/\d{1,2}',  # 2024/01/01
        r'^\d{4}年\d{1,2}月\d{1,2}日',  # 2024年01月01日
        r'^\d{1,2}-\d{1,2}-\d{4}',  # 01-01-2024
        r'^\d{1,2}/\d{1,2}/\d{4}',  # 01/01/2024
    ]
    return any(re.match(p, s) for p in date_patterns)


def _is_phone(s: str) -> bool:
    """判断是否为电话号码"""
    s = str(s).replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    return bool(re.match(r'^1[3-9]\d{9}$', s)) or bool(re.match(r'^\d{7,12}$', s))


def extract_table_from_image(image_bytes: bytes) -> Tuple[List[str], List[List[str]]]:
    """使用 OCR 从图片中提取表格数据"""
    try:
        # 打开图片
        pil_img = Image.open(io.BytesIO(image_bytes))
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')

        # 尝试图像预处理提高 OCR 准确率
        if CV2_AVAILABLE:
            img_array = np.array(pil_img)
            # 灰度化
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # 降噪
            denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
            pil_img_processed = Image.fromarray(denoised)
        else:
            pil_img_processed = pil_img

        # OCR 提取文字（优先中文）
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(pil_img_processed, lang='chi_sim+eng', config=custom_config)

        # 解析表格结构
        lines = text.strip().split('\n')
        headers = []
        rows = []

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            # 分割列（尝试多种分隔符）
            cells = re.split(r'[\t││┌┐└┘├┤┼─=]{2,}', line)
            if len(cells) < 2:
                cells = re.split(r'\s{2,}', line)
            if len(cells) < 2:
                cells = re.split(r'\t', line)

            cells = [c.strip() for c in cells if c.strip()]

            if len(cells) >= 2:
                if i == 0 or any(kw in cells[0] for kw in ['名称', '姓名', '编码', '编号', '类型', '日期', '电话', '金额', '部门', '状态']):
                    # 可能是表头行
                    if not headers or len(cells) > len(headers):
                        headers = cells
                else:
                    rows.append(cells)

        # 如果没识别到表头，从第一行数据推断
        if not headers and rows:
            headers = [f'字段{i+1}' for i in range(len(rows[0]))]

        return headers, rows

    except Exception as e:
        raise Exception(f"OCR识别失败: {str(e)}")


def parse_excel(file_bytes: bytes, filename: str, header_row: int = 0, sheet_name: str = None) -> Dict[str, Any]:
    """解析 Excel/CSV 文件，返回表头和数据
    Args:
        header_row: 指定哪一行作为表头（0=第一行）
        sheet_name: 指定工作表名
    """
    if not EXCEL_AVAILABLE:
        raise Exception("未安装 openpyxl 或 pandas")

    file_obj = io.BytesIO(file_bytes)
    filename_lower = filename.lower()

    try:
        if filename_lower.endswith('.csv'):
            # CSV 先全部读取为字符串
            df = pd.read_csv(file_obj, encoding='utf-8-sig', header=None, dtype=str)
        elif filename_lower.endswith(('.xlsx', '.xls')):
            # 获取所有sheet名
            xl = pd.ExcelFile(file_obj, engine='openpyxl' if filename_lower.endswith('.xlsx') else 'xlrd')
            sheet_names = xl.sheet_names
            actual_sheet = sheet_name if sheet_name and sheet_name in sheet_names else sheet_names[0]
            df = pd.read_excel(xl, sheet_name=actual_sheet, header=None, dtype=str)
        else:
            raise Exception("不支持的文件格式，请上传 .xlsx/.xls/.csv 文件")

        # 填充NaN
        df = df.fillna('')

        # 获取所有行的原始数据（供前端选择表头行）
        all_rows_raw = df.astype(str).values.tolist()

        # 过滤空行
        all_rows = [r for r in all_rows_raw if any(c.strip() for c in r)]

        # 获取sheet列表（仅Excel）
        sheet_names = []
        if not filename_lower.endswith('.csv'):
            try:
                file_obj.seek(0)
                xl2 = pd.ExcelFile(file_obj, engine='openpyxl' if filename_lower.endswith('.xlsx') else 'xlrd')
                sheet_names = xl2.sheet_names
            except Exception:
                pass

        # 根据 header_row 提取表头
        if header_row < 0 or header_row >= len(all_rows):
            header_row = 0

        headers = [str(c).strip() for c in all_rows[header_row]]
        # 数据行 = 表头行之后的所有行
        rows = all_rows[header_row + 1:]
        rows = [r for r in rows if any(c.strip() for c in r)]

        return {
            'success': True,
            'headers': headers,
            'rows': rows,
            'all_rows': all_rows,  # 所有行原始数据，供前端选择表头行
            'total_rows': len(rows),
            'total_columns': len(headers),
            'sheet_name': sheet_names[0] if sheet_names else 'Sheet1',
            'sheet_names': sheet_names,  # 所有工作表名
            'header_row': header_row
        }
    except UnicodeDecodeError:
        # 尝试 GBK 编码
        file_obj.seek(0)
        if filename_lower.endswith('.csv'):
            df = pd.read_csv(file_obj, encoding='gbk', header=None, dtype=str)
        else:
            df = pd.read_excel(file_obj, encoding='gbk', header=None, dtype=str)
        df = df.fillna('')
        all_rows_raw = df.astype(str).values.tolist()
        all_rows = [r for r in all_rows_raw if any(c.strip() for c in r)]

        if header_row < 0 or header_row >= len(all_rows):
            header_row = 0
        headers = [str(c).strip() for c in all_rows[header_row]]
        rows = all_rows[header_row + 1:]
        rows = [r for r in rows if any(c.strip() for c in r)]

        return {
            'success': True,
            'headers': headers,
            'rows': rows,
            'all_rows': all_rows,
            'total_rows': len(rows),
            'total_columns': len(headers),
            'sheet_name': 'Sheet1',
            'sheet_names': [],
            'header_row': header_row
        }


def generate_fields_from_data(headers: List[str], rows: List[List[str]] = None) -> List[Dict[str, Any]]:
    """根据表头和示例数据自动生成字段定义"""
    fields = []
    existing_names = set()

    for i, header in enumerate(headers):
        header_clean = header.strip()
        if not header_clean:
            continue

        # 生成字段名
        base_name = chinese_to_pinyin(header_clean)
        field_name = base_name
        counter = 1
        while field_name in existing_names:
            field_name = f"{base_name}_{counter}"
            counter += 1
        existing_names.add(field_name)

        # 获取该列的示例值
        col_values = []
        if rows:
            for row in rows:
                if i < len(row):
                    col_values.append(row[i])

        # 推断字段类型
        field_type = infer_field_type(header_clean, col_values)

        # 生成选项（如果是选择类型）
        options = []
        options_text = ''
        if field_type == 'select' and col_values:
            unique_vals = list(set(v.strip() for v in col_values if v.strip()))[:20]
            options = unique_vals
            options_text = '，'.join(unique_vals)

        # 判断是否必填（第一行通常是表头，不是数据）
        required = False

        field_def = {
            'name': field_name,
            'label': header_clean,
            'type': field_type,
            'placeholder': f'请输入{header_clean}' if field_type == 'text' else '',
            'required': required,
            'width': '100%',
            'options': options,
            'optionsText': options_text,
            'min': 0,
            'max': 100,
            'maxLength': 255,
        }
        fields.append(field_def)

    return fields


def enhance_with_jieba(headers: List[str], rows: List[List[str]] = None) -> Dict[str, Any]:
    """使用 jieba 分词增强分析表头语义"""
    if not JIEBA_AVAILABLE:
        return {}

    analysis = {}
    for header in headers:
        header = header.strip()
        if not header:
            continue

        # jieba 词性标注
        words = jieba.cut(header)
        word_pos = jieba.posseg.cut(header)

        keywords = []
        for w, flag in word_pos:
            if len(w) > 1 and flag in ('n', 'nr', 'ns', 'nt', 'nz', 'v', 'an'):
                keywords.append({'word': w, 'pos': flag})

        # TF-IDF 关键词
        try:
            tfidf_tags = jieba.analyse.extract_tags(header, topK=3, withWeight=True)
        except Exception:
            tfidf_tags = []

        # 建议的字段名
        suggested_name = FIELD_NAME_MAP.get(header, chinese_to_pinyin(header))

        analysis[header] = {
            'keywords': keywords,
            'tfidf': tfidf_tags,
            'suggested_field_name': suggested_name,
            'suggested_type': infer_field_type(header, None)
        }

    return analysis


def build_preview_table(headers: List[str], rows: List[List[str]], fields: List[Dict], max_rows: int = 10) -> Dict[str, Any]:
    """构建预览数据"""
    preview_rows = rows[:max_rows]
    preview_data = []

    for row in preview_rows:
        row_data = {}
        for i, field in enumerate(fields):
            if i < len(row):
                row_data[field['name']] = row[i]
            else:
                row_data[field['name']] = ''
        preview_data.append(row_data)

    return {
        'headers': headers,
        'columns': [f['label'] for f in fields],
        'field_types': [f['type'] for f in fields],
        'rows': preview_data,
        'total_count': len(rows)
    }


def export_template_json(name: str, description: str, category: str, fields: List[Dict], filename: str = '') -> Dict[str, Any]:
    """导出为模板 JSON"""
    return {
        'name': name or filename.replace('.xlsx', '').replace('.xls', '').replace('.csv', ''),
        'description': description or f'从 {filename} 导入',
        'category': category or 'general',
        'fields': fields,
        'import_source': filename,
        'created_at': datetime.now().isoformat(),
        'version': '1.0'
    }
