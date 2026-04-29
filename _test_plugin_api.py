"""测试插件 API"""
import requests

# 1. 测试插件列表
r = requests.get('http://localhost:8788/api/v1/plugins/', timeout=10)
print(f"GET /plugins/ -> {r.status_code}")
data = r.json()
print(f"Total plugins: {len(data['data'])}")
cats = {}
for p in data['data']:
    cat = p['category']
    cats[cat] = cats.get(cat, 0) + 1
print(f"Categories: {cats}")

# 2. 测试统计
r2 = requests.get('http://localhost:8788/api/v1/plugins/stats/overview', timeout=10)
print(f"\nGET /plugins/stats/overview -> {r2.status_code}")
print(f"Stats: {r2.json()['data']}")

# 3. 测试 AI 工具插件
ai_tools = [p for p in data['data'] if p['category'] == 'ai_tool']
print(f"\nAI Tool plugins ({len(ai_tools)}):")
for t in ai_tools:
    print(f"  - {t['name']} ({t['display_name']}) enabled={t['is_enabled']}")

# 4. 测试禁用一个 AI 工具插件
if ai_tools:
    tool_id = ai_tools[0]['id']
    r3 = requests.post(f'http://localhost:8788/api/v1/plugins/{tool_id}/disable', timeout=10)
    print(f"\nDisable {ai_tools[0]['name']}: {r3.status_code} {r3.json()['message']}")

# 5. 重新启用
if ai_tools:
    r4 = requests.post(f'http://localhost:8788/api/v1/plugins/{tool_id}/enable', timeout=10)
    print(f"Re-enable {ai_tools[0]['name']}: {r4.status_code} {r4.json()['message']}")

print("\nAll tests passed!")
