"""
测试脚本：验证应用属性绑定数据丢失问题是否修复
"""
import requests
import json
import sys

# 配置
BASE_URL = "http://localhost:8879/api/v1"
TEST_APP_ID = 1  # 修改为实际的应用ID

def test_get_app():
    """测试 GET /apps/{id} 是否返回绑定字段"""
    print("=" * 60)
    print("测试 1: GET /apps/{id} 返回绑定字段")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/apps/{TEST_APP_ID}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"返回字段: {list(data.keys())}")
            
            # 检查关键字段
            required_fields = [
                "workflow_ids",
                "workflow_config",
                "knowledge_base_ids",
                "knowledge_config",
                "bound_agents"
            ]
            
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                print(f"❌ 缺失字段: {missing_fields}")
                return False
            else:
                print("✅ 所有绑定字段都存在")
                print(f"  - workflow_ids: {data.get('workflow_ids')}")
                print(f"  - knowledge_base_ids: {data.get('knowledge_base_ids')}")
                print(f"  - bound_agents: {data.get('bound_agents')}")
                return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_update_app():
    """测试 PUT /apps/{id} 是否能更新绑定字段"""
    print("\n" + "=" * 60)
    print("测试 2: PUT /apps/{id} 更新绑定字段")
    print("=" * 60)
    
    # 先获取当前数据
    try:
        response = requests.get(f"{BASE_URL}/apps/{TEST_APP_ID}")
        if response.status_code != 200:
            print(f"❌ 获取应用失败: {response.text}")
            return False
        
        current_data = response.json()
        print(f"当前数据: workflow_ids={current_data.get('workflow_ids')}, knowledge_base_ids={current_data.get('knowledge_base_ids')}")
        
        # 更新绑定字段
        update_data = {
            "workflow_ids": [1, 2, 3],
            "knowledge_base_ids": [10, 20],
            "bound_agents": [100, 200]
        }
        
        response = requests.put(f"{BASE_URL}/apps/{TEST_APP_ID}", json=update_data)
        print(f"更新状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 更新成功")
            print(f"  - workflow_ids: {data.get('workflow_ids')}")
            print(f"  - knowledge_base_ids: {data.get('knowledge_base_ids')}")
            print(f"  - bound_agents: {data.get('bound_agents')}")
            
            # 验证更新是否生效
            if data.get('workflow_ids') == [1, 2, 3]:
                print("✅ 数据保存正确")
                return True
            else:
                print("❌ 数据保存不正确")
                return False
        else:
            print(f"❌ 更新失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_refresh():
    """测试刷新后数据是否还在"""
    print("\n" + "=" * 60)
    print("测试 3: 刷新后数据是否丢失")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/apps/{TEST_APP_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"刷新后数据:")
            print(f"  - workflow_ids: {data.get('workflow_ids')}")
            print(f"  - knowledge_base_ids: {data.get('knowledge_base_ids')}")
            print(f"  - bound_agents: {data.get('bound_agents')}")
            
            # 验证数据是否还在
            if data.get('workflow_ids') == [1, 2, 3]:
                print("✅ 刷新后数据未丢失")
                return True
            else:
                print("❌ 刷新后数据丢失")
                return False
        else:
            print(f"❌ 获取应用失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("应用属性绑定数据丢失问题 - 验证测试")
    print("=" * 60)
    
    # 运行测试
    test1_result = test_get_app()
    test2_result = test_update_app()
    test3_result = test_refresh()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"测试 1 (GET 返回字段): {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"测试 2 (PUT 更新字段): {'✅ 通过' if test2_result else '❌ 失败'}")
    print(f"测试 3 (刷新不丢失): {'✅ 通过' if test3_result else '❌ 失败'}")
    
    if all([test1_result, test2_result, test3_result]):
        print("\n✅ 所有测试通过！修复成功！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
