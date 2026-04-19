"""
我的应用模块 - 数据库迁移脚本
用于创建 applications, app_menus, form_relations, app_plugins 表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import engine

def create_tables():
    """创建我的应用模块所需的表"""
    print("开始创建我的应用模块的数据库表...")
    
    # 导入模型（这会注册表）
    from app.modules.my_apps.models import Application, AppMenu, FormRelation, AppPlugin
    from app.models.user import User
    from app.models.workflow import Template
    
    # 创建表
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    
    print("✅ 表创建成功！")
    print("  - applications (应用表)")
    print("  - app_menus (应用菜单表)")
    print("  - form_relations (表单关系表)")
    print("  - app_plugins (应用插件表)")

if __name__ == "__main__":
    try:
        create_tables()
        print("\n迁移完成！")
    except Exception as e:
        print(f"\n迁移失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
