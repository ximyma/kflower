"""测试插件 seed 流程"""
import sys
sys.path.insert(0, '.')

# 创建同步引擎
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 读取配置
from app.core.config import settings
sync_url = settings.DATABASE_URL
if sync_url.startswith('sqlite+aiosqlite://'):
    sync_url = sync_url.replace('sqlite+aiosqlite://', 'sqlite://', 1)

engine_sync = create_engine(sync_url, echo=True)
SyncSession = sessionmaker(bind=engine_sync, expire_on_commit=False)
db = SyncSession()

try:
    from app.models.plugin import Plugin, PluginHook, seed_builtin_hooks
    print('Models imported OK')
    
    # 尝试 seed hooks
    seed_builtin_hooks(db)
    print('seed_builtin_hooks completed')
    
    # 检查 hooks 数量
    hook_count = db.query(PluginHook).count()
    print(f'Hook count after seed: {hook_count}')
    
    # 尝试添加插件
    from app.core.plugin_manager import BUILTIN_PLUGINS
    print(f'BUILTIN_PLUGINS count: {len(BUILTIN_PLUGINS)}')
    
    for plugin_def in BUILTIN_PLUGINS:
        existing = db.query(Plugin).filter_by(name=plugin_def['name']).first()
        if not existing:
            print(f'Adding plugin: {plugin_def["name"]}')
            db.add(Plugin(**plugin_def))
    
    db.commit()
    print('Commit completed')
    
    # 验证
    final_count = db.query(Plugin).count()
    print(f'Final plugin count: {final_count}')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
