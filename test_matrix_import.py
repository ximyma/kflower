"""
测试矩阵表格导入功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 测试数据：矩阵表格
#         Q1   Q2   Q3
# 产品A   100  150  120
# 产品B   200  180  220
# 总计    300  330  340

all_rows = [
    ["产品/季度", "Q1", "Q2", "Q3"],
    ["产品A", "100", "150", "120"],
    ["产品B", "200", "180", "220"],
    ["总计", "300", "330", "340"]
]

def test_matrix_import():
    """测试矩阵表格导入的完整流程"""
    
    # 1. 测试 parse 端点（解析矩阵表格）
    print("=== 测试 1: POST /api/v1/import/matrix/parse ===")
    try:
        res = requests.post(
            f"{BASE_URL}/api/v1/import/matrix/parse",
            json={
                "all_rows": all_rows,
                "max_row_candidates": 5,
                "max_col_candidates": 5
            },
            headers={"Authorization": "Bearer fake-token-for-test"}
        )
        print(f"状态码: {res.status_code}")
        print(f"响应: {res.text[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 注意：由于需要认证，实际测试需要有效的 token
    print("\n=== 需要有效的认证 token 才能完整测试 ===")
    print("请在前端界面手动测试完整流程。")

if __name__ == "__main__":
    test_matrix_import()
