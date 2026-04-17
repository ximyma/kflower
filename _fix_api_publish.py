# -*- coding: utf-8 -*-
"""
修复模板发布 API 调用
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. 更新前端 API 添加发布方法
api_path = r'D:\kflower\kflower-frontend\src\common\api\index.ts'
with open(api_path, 'r', encoding='utf-8-sig') as f:
    api_content = f.read()

old_template_api = '''  getStats: (id: number) => api.get(`/templates/${id}/stats`),
}'''

new_template_api = '''  getStats: (id: number) => api.get(`/templates/${id}/stats`),
  // 发布模板
  publish: (id: number) => api.post(`/templates/${id}/publish`),
  // 保存模板（兼容旧调用）
  saveTemplate: (id: number | null, data: any) => {
    if (id) {
      return api.put(`/templates/${id}`, data)
    } else {
      return api.post('/templates/', data)
    }
  },
}'''

if old_template_api in api_content:
    api_content = api_content.replace(old_template_api, new_template_api)
    print("[OK] templateAPI 发布方法已添加")

# 保存 API 文件
with open(api_path, 'w', encoding='utf-8-sig') as f:
    f.write(api_content)

# 2. 更新 Templates.vue 中的发布函数调用
tpl_path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(tpl_path, 'r', encoding='utf-8-sig') as f:
    tpl_content = f.read()

# 修复 API 调用：使用 templateAPI 而非 localAPI
old_publish_call = '''    // 调用后端发布 API
    const res = await templateAPI.saveTemplate(tpl.id, publishData)'''

new_publish_call = '''    // 调用后端发布 API（创建或更新）
    let res: any
    if (tpl.id) {
      res = await templateAPI.update(tpl.id, publishData)
    } else {
      res = await templateAPI.create(publishData)
    }
    // 同时调用发布接口
    if (res.data?.id) {
      await templateAPI.publish(res.data.id)
    }'''

if old_publish_call in tpl_content:
    tpl_content = tpl_content.replace(old_publish_call, new_publish_call)
    print("[OK] 发布 API 调用已修复")

# 保存模板文件
with open(tpl_path, 'w', encoding='utf-8-sig') as f:
    f.write(tpl_content)

print("\nAPI 修复完成！")