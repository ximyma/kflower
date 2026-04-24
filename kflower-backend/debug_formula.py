#!/usr/bin/env python
"""调试公式引擎"""
from app.core.formula_engine import formula_engine

# 测试中文
formula = '{单价} * {数量}'
context = {'单价': 100, '数量': 5}

print(f"Formula: {formula}")
print(f"Context: {context}")
print(f"Context types: 单价={type(context['单价'])}, 数量={type(context['数量'])}")

processed, var_map = formula_engine._preprocess(formula, context)
print(f"Processed: {processed}")
print(f"Var map: {var_map}")
print(f"Var map types: {[(k, type(v)) for k, v in var_map.items()]}")

result = formula_engine.evaluate(formula, context)
print(f"Result: {result}")
print(f"Expected: 500")
