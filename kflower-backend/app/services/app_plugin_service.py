"""应用插件服务"""
from typing import Dict, List, Any, Optional
import json
import sqlite3
from app.core.config import settings

class AppPluginService:
    """应用插件服务 - 使用原生SQL操作"""

    @staticmethod
    def _get_db_path():
        """获取数据库路径"""
        return settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")

    @staticmethod
    def _dict_factory(cursor, row):
        """将查询结果转为字典"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @staticmethod
    def get_app_plugins(app_id: int) -> List[Dict[str, Any]]:
        """获取应用绑定的所有插件"""
        db_path = AppPluginService._get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = AppPluginService._dict_factory
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                ap.id, ap.app_id, ap.plugin_id, ap.config, ap.is_enabled, ap.sort_order, ap.created_at,
                p.name as plugin_name, p.display_name, p.description, p.version, 
                p.author, p.icon, p.category, p.hook_code
            FROM app_plugins ap
            JOIN plugins p ON ap.plugin_id = p.id
            WHERE ap.app_id = ?
            ORDER BY ap.sort_order
        ''', (app_id,))
        
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            if row['config']:
                try:
                    row['config'] = json.loads(row['config'])
                except:
                    row['config'] = {}
            else:
                row['config'] = {}
            
            if row['hook_code']:
                try:
                    row['hook_code'] = json.loads(row['hook_code'])
                except:
                    row['hook_code'] = {}
            else:
                row['hook_code'] = {}

        return rows

    @staticmethod
    def bind_plugin(
        app_id: int,
        plugin_id: int,
        config: Optional[Dict[str, Any]] = None,
        sort_order: int = 0
    ) -> Dict[str, Any]:
        """将插件绑定到应用"""
        db_path = AppPluginService._get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = AppPluginService._dict_factory
        cursor = conn.cursor()

        # 检查插件是否存在
        cursor.execute('SELECT id, display_name FROM plugins WHERE id = ?', (plugin_id,))
        plugin = cursor.fetchone()
        if not plugin:
            conn.close()
            return {"success": False, "message": "插件不存在"}

        # 检查是否已绑定
        cursor.execute(
            'SELECT id FROM app_plugins WHERE app_id = ? AND plugin_id = ?',
            (app_id, plugin_id)
        )
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return {"success": False, "message": "该插件已绑定到此应用"}

        # 创建绑定记录
        config_json = json.dumps(config or {})
        cursor.execute('''
            INSERT INTO app_plugins (app_id, plugin_id, name, trigger_event, target_template_id, script_code, config, is_enabled, sort_order, created_at, updated_at)
            VALUES (?, ?, '', '', 0, '', ?, ?, ?, datetime('now'), datetime('now'))
        ''', (app_id, plugin_id, config_json, 1, sort_order))
        
        binding_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"插件 {plugin['display_name']} 已绑定",
            "data": {
                "id": binding_id,
                "plugin_id": plugin_id,
                "app_id": app_id,
            }
        }

    @staticmethod
    def unbind_plugin(app_id: int, binding_id: int) -> Dict[str, Any]:
        """解除插件绑定"""
        db_path = AppPluginService._get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM app_plugins WHERE id = ?', (binding_id,))
        binding = cursor.fetchone()
        if not binding:
            conn.close()
            return {"success": False, "message": "绑定记录不存在"}

        cursor.execute('DELETE FROM app_plugins WHERE id = ?', (binding_id,))
        conn.commit()
        conn.close()

        return {"success": True, "message": "已解除绑定"}

    @staticmethod
    def update_plugin_binding(
        app_id: int,
        binding_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新插件绑定配置"""
        db_path = AppPluginService._get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM app_plugins WHERE id = ?', (binding_id,))
        binding = cursor.fetchone()
        if not binding:
            conn.close()
            return {"success": False, "message": "绑定记录不存在"}

        set_clause = []
        params = []

        if "is_enabled" in updates:
            set_clause.append("is_enabled = ?")
            params.append(1 if updates["is_enabled"] else 0)
        
        if "config" in updates:
            set_clause.append("config = ?")
            params.append(json.dumps(updates["config"]))
        
        if "sort_order" in updates:
            set_clause.append("sort_order = ?")
            params.append(updates["sort_order"])

        if set_clause:
            set_clause.append("updated_at = datetime('now')")
            params.append(binding_id)
            cursor.execute(
                f'UPDATE app_plugins SET {", ".join(set_clause)} WHERE id = ?',
                params
            )
            conn.commit()

        conn.close()
        return {"success": True, "message": "更新成功"}

    @staticmethod
    def get_available_plugins(app_id: int) -> List[Dict[str, Any]]:
        """获取可绑定到应用的插件列表"""
        db_path = AppPluginService._get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = AppPluginService._dict_factory
        cursor = conn.cursor()

        # 获取已绑定的插件ID
        cursor.execute('SELECT plugin_id FROM app_plugins WHERE app_id = ?', (app_id,))
        bound_ids = [row['plugin_id'] for row in cursor.fetchall()]

        if bound_ids:
            placeholders = ','.join('?' * len(bound_ids))
            cursor.execute(f'''
                SELECT id, name, display_name, description, version, author, icon, category, hook_code
                FROM plugins
                WHERE id NOT IN ({placeholders})
            ''', bound_ids)
        else:
            cursor.execute('''
                SELECT id, name, display_name, description, version, author, icon, category, hook_code
                FROM plugins
            ''')

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            if row['hook_code']:
                try:
                    row['hook_code'] = json.loads(row['hook_code'])
                except:
                    row['hook_code'] = {}
            else:
                row['hook_code'] = {}

        return rows

    @staticmethod
    def trigger_app_plugin_hook(app_id: int, hook_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """触发应用插件钩子"""
        db_path = AppPluginService._get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = AppPluginService._dict_factory
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ap.config, p.hook_code
            FROM app_plugins ap
            JOIN plugins p ON ap.plugin_id = p.id
            WHERE ap.app_id = ? AND ap.is_enabled = 1
        ''', (app_id,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            try:
                hook_code = json.loads(row['hook_code']) if row['hook_code'] else {}
                plugin_config = json.loads(row['config']) if row['config'] else {}
                
                if hook_name in hook_code:
                    code = hook_code[hook_name]
                    try:
                        ctx = {
                            **context,
                            'config': plugin_config,
                            'app_id': app_id,
                            'hook_name': hook_name
                        }
                        local_vars = {'ctx': ctx}
                        exec(code, globals(), local_vars)
                        if 'on_event' in local_vars:
                            result = local_vars['on_event'](ctx)
                            results.append({
                                'success': True,
                                'result': result
                            })
                        else:
                            results.append({
                                'success': False,
                                'error': 'hook function not found'
                            })
                    except Exception as e:
                        results.append({
                            'success': False,
                            'error': str(e)
                        })
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e)
                })

        return {
            'hook_name': hook_name,
            'app_id': app_id,
            'results': results,
            'total_triggered': len([r for r in results if r['success']])
        }