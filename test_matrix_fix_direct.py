# -*- coding: utf-8 -*-
"""
直接测试 parse_matrix_table 函数（不需要认证）
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kflower-backend'))

from app.services.import_matrix_service import parse_matrix_table

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

print("=" * 60)
print("直接测试 parse_matrix_table 函数")
print("=" * 60)
print(f"输入数据：")
print(f"  - 总行数：{len(all_rows)}")
for i, row in enumerate(all_rows):
    print(f"  - 第{i+1}行：{row}")

print(f"\n调用参数：")
print(f"  - row_header_row = 0 （第一行是列维度）")
print(f"  - col_header_col = 0 （第一列是行维度）")
print(f"  - merge_type = 'concat'")
print()

try:
    result = parse_matrix_table(
        all_rows=all_rows,
        row_header_row=0,
        col_header_col=0,
        merge_type="concat"
    )
    
    if "error" in result:
        print(f"❌ 错误：{result['error']}")
    else:
        print(f"✅ 转换成功！")
        print(f"\n转换结果：")
        print(f"  - 行维度：{result.get('row_headers')}")
        print(f"  - 列维度：{result.get('col_headers')}")
        print(f"  - 表头：{result.get('headers')}")
        print(f"  - 总数据行数：{result.get('total_rows')}")
        print(f"  - 总列数：{result.get('total_columns')}")
        
        print(f"\n转换后的一维数据（前10行）：")
        for i, row in enumerate(result.get('rows', [])[:10]):
            print(f"  {i+1}. {row}")
        
        print(f"\n字段定义：")
        for field in result.get('fields', []):
            print(f"  - {field['label']} ({field['name']}): {field['type']}")
        
        print(f"\n矩阵预览：")
        preview = result.get('matrix_preview', {})
        print(f"  - 行表头：{preview.get('row_headers')}")
        print(f"  - 列表头：{preview.get('col_headers')}")
        print(f"  - 数据区域：{preview.get('data_region')}")
        
except Exception as e:
    print(f"❌ 异常：{e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
