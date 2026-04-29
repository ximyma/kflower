#!/usr/bin/env python3
"""
测试应用插件绑定功能
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kflower-backend'))

from app.services.app_plugin_service import AppPluginService

def test_bind():
    print("测试绑定插件到应用...")
    
    # 绑定插件 1 到应用 1
    result = AppPluginService.bind_plugin(app_id=1, plugin_id=1)
    print(f"绑定结果: {result}")
    
    # 查询应用 1 的绑定插件
    plugins = AppPluginService.get_app_plugins(app_id=1)
    print(f"应用 1 的绑定插件: {plugins}")
    
    # 查询可绑定的插件
    available = AppPluginService.get_available_plugins(app_id=1)
    print(f"可绑定的插件数量: {len(available)}")

if __name__ == "__main__":
    test_bind()