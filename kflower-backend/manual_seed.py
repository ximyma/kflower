"""手动 seed 内置插件和钩子事件"""
import sys
sys.path.insert(0, '.')

# 先导入所有模型（解决 SQLAlchemy 关系依赖）
import app.models.user
import app.models.workflow
import app.models.ai
import app.models.permission
import app.models.notification_template
import app.models.data_model
import app.models.plugin
import app.models.plugin_binding
import app.modules.my_apps.models

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.models.plugin import Plugin, PluginHook, seed_builtin_hooks
from app.core.plugin_manager import BUILTIN_PLUGINS

# 创建同步引擎
sync_url = settings.DATABASE_URL
if sync_url.startswith('sqlite+aiosqlite://'):
    sync_url = sync_url.replace('sqlite+aiosqlite://', 'sqlite://', 1)

engine_sync = create_engine(sync_url)
SyncSession = sessionmaker(bind=engine_sync, expire_on_commit=False)
db = SyncSession()

try:
    # 1. Seed 内置钩子事件
    print('[1/3] Seeding builtin hooks...')
    seed_builtin_hooks(db)
    
    # 2. 检查并添加内置插件
    print('[2/3] Checking builtin plugins...')
    for plugin_def in BUILTIN_PLUGINS:
        existing = db.query(Plugin).filter_by(name=plugin_def['name']).first()
        if not existing:
            print(f'  Adding plugin: {plugin_def["name"]}')
            plugin = Plugin(**plugin_def)
            plugin.is_installed = True
            plugin.is_enabled = True
            db.add(plugin)
        else:
            print(f'  Already exists: {plugin_def["name"]}')
    
    # 3. 提交
    print('[3/3] Committing...')
    db.commit()
    
    # 4. 验证
    plugin_count = db.query(Plugin).count()
    hook_count = db.query(PluginHook).count()
    print(f'\nDone! Plugins: {plugin_count}, Hooks: {hook_count}')
    
    # 5. 列出插件
    plugins = db.query(Plugin).all()
    for p in plugins:
        print(f'  - {p.name} | {p.display_name} | builtin={p.is_built_in}')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
