"""
迁移脚本：为 roles 表添加缺失的 data_permission_rules 列

问题：Role 模型定义了 data_permission_rules 字段，但数据库表未创建该列，
导致注册用户时查询 roles 表报 OperationalError。

运行方式：python -m migrations.add_role_data_permission_rules
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kflower-data', 'kflower.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute('PRAGMA table_info(roles)')
    cols = [r[1] for r in cur.fetchall()]

    if 'data_permission_rules' in cols:
        print('[SKIP] roles.data_permission_rules 已存在')
    else:
        conn.execute("ALTER TABLE roles ADD COLUMN data_permission_rules TEXT DEFAULT '[]'")
        conn.commit()
        print('[OK] roles.data_permission_rules 已添加')

    conn.close()


if __name__ == '__main__':
    migrate()
