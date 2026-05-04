# -*- coding: utf-8 -*-
"""
测试修复后的矩阵表格导入API
"""
import requests
import json

# 测试数据：4行×4列矩阵表格
#        Q1    Q2    Q3
# 产品A   100   150   120
# 产品B   200   180   220
# 总计    300   330   340

all_rows = [
    ["", "Q1", "Q2", "Q3"],
    ["产品A", "100", "150", "120"],
    ["产品B", "200", "180", "220"],
    ["总计", "300", "330", "340"]
]

# 测试 /api/v1/import/matrix/apply-header
url = "http://localhost:8000/api/v1/import/matrix/apply-header"
headers = {
    "Content-Type": "application/json"
}
data = {
    "all_rows": all_rows,
    "row_header_row": 0,
    "col_header_col": 0,
    "merge_type": "concat"
}

print("=" * 60)
print("测试 /api/v1/import/matrix/apply-header")
print("=" * 60)
print(f"请求数据：")
print(f"  - 总行数：{len(all_rows)}")
print(f"  - 行表头行：{data['row_header_row']}")
print(f"  - 列表头列：{data['col_header_col']}")
print()

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"成功：{result.get('success')}")
        print(f"消息：{result.get('message')}")
        
        data = result.get('data', {})
        print(f"\n转换结果：")
        print(f"  - 行维度：{data.get('row_headers')}")
        print(f"  - 列维度：{data.get('col_headers')}")
        print(f"  - 表头：{data.get('headers')}")
        print(f"  - 总数据行数：{data.get('total_rows')}")
        print(f"  - 总列数：{data.get('total_columns')}")
        
        print(f"\n前5行数据：")
        for i, row in enumerate(data.get('rows', [])[:5]):
            print(f"  {i+1}. {row}")
        
        print(f"\n字段定义：")
        for field in data.get('fields', []):
            print(f"  - {field['label']} ({field['name']}): {field['type']}")
        
    else:
        print(f"错误：{response.text}")
        
except Exception as e:
    print(f"异常：{e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
