"""
修复 AI 生成但未发布的模板
直接通过 SQL 发布模板并创建数据表
"""
import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"


def get_field_sql_type(field_type):
    """获取字段对应的 SQL 类型"""
    if field_type in ('number', 'money', 'percent'):
        return 'REAL'
    elif field_type in ('date', 'datetime'):
        return 'TEXT'
    elif field_type in ('switch', 'checkbox'):
        return 'INTEGER DEFAULT 0'
    else:
        return 'TEXT'


def safe_column_name(field_name):
    """安全的列名"""
    safe = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(field_name))
    if safe and safe[0].isdigit():
        safe = 'f_' + safe
    return safe


def publish_template(db, template_id, template_name, config_json, modules_json):
    """发布单个模板"""
    # 解析配置
    config = json.loads(config_json) if isinstance(config_json, str) else (config_json or {})
    modules = json.loads(modules_json) if isinstance(modules_json, str) else (modules_json or [])
    
    # 收集所有字段
    all_fields = []
    for mod in modules:
        if isinstance(mod, dict) and 'fields' in mod:
            all_fields.extend(mod.get('fields', []))
    
    # 构建建表语句
    columns = [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "template_id INTEGER NOT NULL",
        "created_by INTEGER",
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP",
    ]
    
    for field in all_fields:
        if not isinstance(field, dict):
            continue
        field_name = field.get('name', '')
        if not field_name:
            continue
        
        field_type = field.get('type', 'text')
        
        # 跳过特殊类型
        if field_type == 'subform' or field.get('is_formula'):
            continue
        
        safe_name = safe_column_name(field_name)
        col_type = get_field_sql_type(field_type)
        columns.append(f'"{safe_name}" {col_type}')
    
    # 创建表
    table_name = f"form_data_{template_id}"
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
    
    cursor = db.cursor()
    cursor.execute(create_sql)
    
    # 更新配置中的表名
    config['table_name'] = table_name
    cursor.execute(
        "UPDATE templates SET config = ?, is_published = 1 WHERE id = ?",
        (json.dumps(config), template_id)
    )
    
    db.commit()
    return table_name


def fix_all_unpublished():
    """修复所有未发布的模板"""
    conn = sqlite3.connect(DATABASE_PATH)
    
    # 查找未发布的模板
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, code, config, modules 
        FROM templates 
        WHERE is_published = 0 
        ORDER BY id
    """)
    templates = cursor.fetchall()
    
    logger.info(f"找到 {len(templates)} 个未发布的模板")
    
    published_count = 0
    error_count = 0
    
    for template in templates:
        template_id, name, code, config, modules = template
        try:
            logger.info(f"正在发布: {name} (ID: {template_id})")
            
            # 检查是否已有数据表
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='form_data_{template_id}'")
            if cursor.fetchone():
                logger.info(f"  数据表已存在，跳过建表")
            else:
                table_name = publish_template(conn, template_id, name, config, modules)
                logger.info(f"  创建数据表: {table_name}")
            
            published_count += 1
            logger.info(f"✓ 模板 {name} 发布成功")
        except Exception as e:
            error_count += 1
            logger.error(f"✗ 模板 {name} 发布失败: {e}")
    
    conn.close()
    
    logger.info(f"=" * 50)
    logger.info(f"完成！成功发布 {published_count} 个模板，失败 {error_count} 个")
    
    # 验证结果
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM templates WHERE is_published = 1")
    published = cursor.fetchone()[0]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'form_data_%'")
    tables = cursor.fetchall()
    
    logger.info(f"验证结果：")
    logger.info(f"  已发布模板: {published} 个")
    logger.info(f"  动态数据表: {len(tables)} 个")
    
    conn.close()


if __name__ == "__main__":
    fix_all_unpublished()
