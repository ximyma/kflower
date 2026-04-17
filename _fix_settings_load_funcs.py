# -*- coding: utf-8 -*-
"""
修复 Settings.vue - 添加缺失的加载函数
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 添加响应式对象
old_basic = '''const basicSettings = reactive({'''
if old_basic not in content:
    # 在合适的位置添加
    insert_point = 'const embedModelForm = reactive({'
    new_vars = '''const basicSettings = reactive({ platformName: 'Kflower 企业智能管理平台', description: '' })
const moduleAISettings = reactive({
  chatGeneral: '', chatTemplate: '', chatWorkflow: '', chatAnalytics: '',
  ragModel: '', processingModel: ''
})
const ocrConfig = reactive({ tesseractPath: 'D:\\\\Tesseract-OCR\\\\tesseract.exe', lang: 'chi_sim+eng' })

'''
    if insert_point in content:
        content = content.replace(insert_point, new_vars + insert_point)
        print("[OK] 响应式对象已添加")

# 2. 添加加载函数
old_load_embed_config = '''async function loadEmbedConfig() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.embedding_api_key) embedConfig.apiKey = config.embedding_api_key
    if (config.embedding_base_url) embedConfig.apiBase = config.embedding_base_url
    if (config.embedding_model) embedConfig.model = config.embedding_model
  } catch { /* ignore */ }
}'''

new_load_funcs = '''async function loadEmbedConfig() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.embedding_api_key) embedConfig.apiKey = config.embedding_api_key
    if (config.embedding_base_url) embedConfig.apiBase = config.embedding_base_url
    if (config.embedding_model) embedConfig.model = config.embedding_model
  } catch { /* ignore */ }
}

async function loadBasicSettings() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.platform_name) basicSettings.platformName = config.platform_name
    if (config.platform_description) basicSettings.description = config.platform_description
  } catch { /* ignore */ }
}

async function loadModuleAISettings() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.module_ai_settings) {
      const settings = typeof config.module_ai_settings === 'string' 
        ? JSON.parse(config.module_ai_settings) 
        : config.module_ai_settings
      Object.assign(moduleAISettings, settings)
    }
  } catch { /* ignore */ }
}

async function loadOCRConfig() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.ocr_tesseract_path) ocrConfig.tesseractPath = config.ocr_tesseract_path
    if (config.ocr_lang) ocrConfig.lang = config.ocr_lang
  } catch { /* ignore */ }
}

async function saveBasicSettings() {
  saving.value = true
  try {
    await systemAPI.saveConfig({ platform_name: basicSettings.platformName, platform_description: basicSettings.description })
    ElMessage.success('基本设置已保存')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}'''

if old_load_embed_config in content:
    content = content.replace(old_load_embed_config, new_load_funcs)
    print("[OK] 加载函数已添加")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\n修复完成！")