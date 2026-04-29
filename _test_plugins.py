#!/usr/bin/env python3
"""
测试插件API
"""
import requests
import json

BASE_URL = "http://localhost:8788/api/v1"

def test_plugins_api():
    # 首先尝试登录获取token
    print("1. 测试登录获取token...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   登录响应: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            token = data.get("data", {}).get("access_token") or data.get("access_token")
            print(f"   获取到token: {token[:20]}..." if token else "   无token")

            headers = {"Authorization": f"Bearer {token}"}

            # 测试获取插件列表
            print("\n2. 测试获取插件列表...")
            resp = requests.get(f"{BASE_URL}/plugins/", headers=headers)
            print(f"   状态码: {resp.status_code}")
            print(f"   响应: {resp.text[:500]}")

            # 测试获取统计
            print("\n3. 测试获取统计...")
            resp = requests.get(f"{BASE_URL}/plugins/stats/overview", headers=headers)
            print(f"   状态码: {resp.status_code}")
            print(f"   响应: {resp.text[:500]}")

            # 测试获取内置事件
            print("\n4. 测试获取内置事件...")
            resp = requests.get(f"{BASE_URL}/plugins/builtin-events", headers=headers)
            print(f"   状态码: {resp.status_code}")
            print(f"   响应: {resp.text[:500]}")

        else:
            print(f"   登录失败: {resp.text}")

    except Exception as e:
        print(f"   错误: {e}")

if __name__ == "__main__":
    test_plugins_api()
