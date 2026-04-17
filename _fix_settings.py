# -*- coding: utf-8 -*-
"""Fix Settings.vue: don't JSON.stringify ai_models and ai_params"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix 1: saveConfig in add/edit model
old1 = "ai_models: JSON.stringify(configuredModels.value),"
new1 = "ai_models: configuredModels.value,"
count1 = content.count(old1)
print(f"Found {count1} occurrences of JSON.stringify(configuredModels.value)")

if count1 > 0:
    content = content.replace(old1, new1)

# Fix 2: JSON.stringify(params) 
old2 = "ai_params: JSON.stringify(params)"
new2 = "ai_params: params"
count2 = content.count(old2)
print(f"Found {count2} occurrences of JSON.stringify(params)")

if count2 > 0:
    content = content.replace(old2, new2)

# Fix 3: deleteModel also uses JSON.stringify
old3 = "ai_models: JSON.stringify(configuredModels.value)"
new3 = "ai_models: configuredModels.value"
count3 = content.count(old3)
print(f"Found {count3} occurrences in deleteModel")

if count3 > 0:
    content = content.replace(old3, new3)

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\nSettings.vue fixed!")
