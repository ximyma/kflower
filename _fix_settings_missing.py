# -*- coding: utf-8 -*-
"""
修复 Settings.vue - 添加缺失的函数
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 添加 loadEmbedConfig 函数
old_test_ocr = '''async function testOCR() {
  testingOCR.value = true
  ElMessage.info('请上传图片测试 OCR 识别（功能已就绪）')
  testingOCR.value = false
}'''

new_test_ocr = '''async function testOCR() {
  testingOCR.value = true
  ElMessage.info('请上传图片测试 OCR 识别（功能已就绪）')
  testingOCR.value = false
}

async function loadEmbedConfig() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.embedding_api_key) embedConfig.apiKey = config.embedding_api_key
    if (config.embedding_base_url) embedConfig.apiBase = config.embedding_base_url
    if (config.embedding_model) embedConfig.model = config.embedding_model
  } catch { /* ignore */ }
}'''

if old_test_ocr in content:
    content = content.replace(old_test_ocr, new_test_ocr)
    print("[OK] loadEmbedConfig 函数已添加")

# 2. 更新 onMounted
old_mount = '''onMounted(async () => {
  await Promise.all([loadProviders(), loadConfiguredModels(), loadServicesStatus(), loadEmbedModels()])
})'''

new_mount = '''onMounted(async () => {
  await Promise.all([
    loadProviders(), 
    loadConfiguredModels(), 
    loadServicesStatus(), 
    loadEmbedModels(),
    loadEmbedConfig(),
    loadBasicSettings(),
    loadModuleAISettings(),
    loadOCRConfig(),
    loadConfiguredEmbedModels(),
    loadConfiguredRerankModels(),
  ])
})'''

if old_mount in content:
    content = content.replace(old_mount, new_mount)
    print("[OK] onMounted 已更新")
else:
    print("[WARN] onMounted 未找到，可能已更新")

# 3. 添加缺失的函数引用
# 检查是否有 loadConfiguredEmbedModels
if 'loadConfiguredEmbedModels' not in content:
    print("[WARN] 需要添加 loadConfiguredEmbedModels 等函数")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\n修复完成！")