#!/usr/bin/env python3
"""测试插件API"""
import requests

BASE_URL = "http://localhost:8788/api/v1"

# 登录获取token
login_data = {
    "username": "admin",
    "password": "admin123"
}

try:
    print("1. 登录获取token...")
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("data", {}).get("access_token") or data.get("access_token")
        print(f"   获取到token: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试插件列表API
        print("\n2. 测试插件列表API...")
        resp = requests.get(f"{BASE_URL}/plugins/", headers=headers)
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.text[:500]}")
        
        # 测试模板插件API
        print("\n3. 测试模板插件API...")
        resp = requests.get(f"{BASE_URL}/templates/1/plugins", headers=headers)
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.text[:500]}")
        
    else:
        print(f"   登录失败: {resp.text}")
except Exception as e:
    print(f"   错误: {e}")
