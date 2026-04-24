#!/usr/bin/env python
"""智能表单公式引擎测试"""
from app.core.formula_engine import formula_engine, validation_engine, visibility_engine

print("=" * 50)
print("Formula Engine Tests")
print("=" * 50)

# 1. 基础计算
r1 = formula_engine.evaluate('{单价} * {数量}', {'单价': 100, '数量': 5})
print(f"1. Basic: {{单价}} * {{数量}} = {r1} (expected: 500)")
assert r1 == 500, f"Expected 500, got {r1}"

# 2. 子表聚合
r2 = formula_engine.evaluate('SUM({items.amt})', {'items': [{'amt': 10}, {'amt': 20}, {'amt': 30}]})
print(f"2. Subtable SUM: SUM({{items.amt}}) = {r2} (expected: 60)")
assert r2 == 60, f"Expected 60, got {r2}"

# 3. ROUND 函数
r3 = formula_engine.evaluate('ROUND({price} * 0.13, 2)', {'price': 100})
print(f"3. ROUND: ROUND({{price}} * 0.13, 2) = {r3} (expected: 13.0)")
assert r3 == 13.0, f"Expected 13.0, got {r3}"

# 4. IF 函数
r4 = formula_engine.evaluate('IF({age} >= 18, "adult", "minor")', {'age': 20})
print(f"4. IF: IF({{age}} >= 18, 'adult', 'minor') = {r4} (expected: adult)")
assert r4 == "adult", f"Expected 'adult', got {r4}"

# 5. CONCAT 函数
r5 = formula_engine.evaluate('CONCAT({first}, "-", {last})', {'first': 'John', 'last': 'Doe'})
print(f"5. CONCAT: CONCAT({{first}}, '-', {{last}}) = {r5} (expected: John-Doe)")
assert r5 == "John-Doe", f"Expected 'John-Doe', got {r5}"

# 6. 链式公式
ctx = {'单价': 100, '数量': 5}
total = formula_engine.evaluate('{单价} * {数量}', ctx)
ctx['总价'] = total
tax = formula_engine.evaluate('ROUND({总价} * 0.13, 2)', ctx)
ctx['税额'] = tax
total_with_tax = formula_engine.evaluate('{总价} + {税额}', ctx)
print(f"6. Chain: total={total}, tax={tax}, total_with_tax={total_with_tax}")
assert total == 500 and tax == 65.0 and total_with_tax == 565.0

# 7. AVG 函数
r7 = formula_engine.evaluate('AVG({scores})', {'scores': [80, 90, 100]})
print(f"7. AVG: AVG({{scores}}) = {r7} (expected: 90)")
assert r7 == 90, f"Expected 90, got {r7}"

# 8. MAX/MIN 函数
r8a = formula_engine.evaluate('MAX({scores})', {'scores': [80, 90, 100]})
r8b = formula_engine.evaluate('MIN({scores})', {'scores': [80, 90, 100]})
print(f"8. MAX/MIN: MAX={{80,90,100}}={r8a}, MIN={{80,90,100}}={r8b}")
assert r8a == 100 and r8b == 80

# 9. TODAY/NOW 函数
r9a = formula_engine.evaluate('TODAY()', {})
r9b = formula_engine.evaluate('NOW()', {})
print(f"9. TODAY/NOW: TODAY()={r9a}, NOW()={r9b}")
assert len(r9a) > 0 and len(r9b) > 0

# 10. LEN 函数
r10 = formula_engine.evaluate('LEN({text})', {'text': 'Hello'})
print(f"10. LEN: LEN({{text}}) = {r10} (expected: 5)")
assert r10 == 5, f"Expected 5, got {r10}"

print("\n" + "=" * 50)
print("All formula engine tests passed!")
print("=" * 50)
