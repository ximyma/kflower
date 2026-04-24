#!/usr/bin/env python
"""智能表单 API 测试"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def test_api_endpoints():
    """测试智能表单相关 API 端点"""
    print("=" * 60)
    print("API Endpoints Test")
    print("=" * 60)
    
    # 1. 测试数据库连接
    print("\n1. Testing database connection...")
    try:
        from app.core.database import get_db
        print("   OK: Database module imported")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # 2. 测试 SubTableData 模型
    print("\n2. Testing SubTableData model...")
    try:
        from app.models.workflow import SubTableData
        print(f"   OK: SubTableData model loaded")
        print(f"   - Table name: {SubTableData.__tablename__}")
        print(f"   - Columns: {[c.name for c in SubTableData.__table__.columns]}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # 3. 测试公式引擎 API
    print("\n3. Testing formula engine API...")
    try:
        from app.core.formula_engine import formula_engine
        result = formula_engine.evaluate('{a} + {b}', {'a': 1, 'b': 2})
        assert result == 3, f"Expected 3, got {result}"
        print(f"   OK: Formula evaluation works ({result})")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # 4. 测试校验引擎
    print("\n4. Testing validation engine...")
    try:
        from app.core.formula_engine import validation_engine
        field_def = {
            'name': 'age',
            'label': '年龄',
            'validation_rules': [
                {'type': 'min_value', 'value': 0, 'message': '年龄不能小于 0'}
            ]
        }
        errors = validation_engine.validate_field(field_def, -5, {})
        assert len(errors) > 0, "Should have validation errors"
        print(f"   OK: Validation engine works (errors: {errors})")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # 5. 测试可见性引擎
    print("\n5. Testing visibility engine...")
    try:
        from app.core.formula_engine import visibility_engine
        field_def = {
            'name': 'vip_field',
            'visibility_rule': {
                'type': 'simple',
                'field': 'user_type',
                'operator': 'eq',
                'value': 'VIP'
            }
        }
        visible = visibility_engine.is_visible(field_def, {'user_type': 'VIP'})
        assert visible == True, "Should be visible for VIP"
        print(f"   OK: Visibility engine works (visible={visible})")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # 6. 测试级联选项引擎
    print("\n6. Testing cascade engine...")
    try:
        from app.core.formula_engine import cascade_engine
        field_def = {
            'name': 'city',
            'cascade_source': {
                'parent_field': 'province',
                'options_map': {
                    '广东': ['广州', '深圳', '东莞'],
                    '浙江': ['杭州', '宁波', '温州']
                }
            }
        }
        options = cascade_engine.get_options(field_def, {'province': '广东'})
        assert '广州' in options, "Should have Guangzhou in options"
        print(f"   OK: Cascade engine works (options: {options})")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # 7. 测试 Templates API 路由
    print("\n7. Testing Templates API router...")
    try:
        from app.api.v1.endpoints.templates import router
        print(f"   OK: Templates router loaded")
        print(f"   - Router prefix: {router.prefix}")
        print(f"   - Router tags: {router.tags}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    print("\n" + "=" * 60)
    print("All API tests passed!")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test_api_endpoints())
