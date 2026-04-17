# -*- coding: utf-8 -*-
"""
Update Settings.vue - improve AI configuration
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 修改 testAIConnection 函数，使用新的 systemAPI.testAI
old_test = '''const testAIConnection = async () => {
  testing.value = true
  try {
    const res: any = await aiAPI.listProviders()
    aiStatus.connected = true
    aiStatus.provider = aiSettings.provider
    ElMessage.success('AI 连接测试成功')
  } catch (e: any) {
    aiStatus.connected = false
    ElMessage.error('连接失败，请检查 API Key')
  } finally {
    testing.value = false
  }
}'''

new_test = '''const testAIConnection = async () => {
  testing.value = true
  try {
    // 先保存配置
    await systemAPI.saveConfig({
      ai_provider: aiSettings.provider,
      ai_api_key: aiSettings.apiKey,
      ai_model: aiSettings.model
    })
    // 测试连接
    const res: any = await systemAPI.testAI()
    if (res.success) {
      aiStatus.connected = true
      aiStatus.provider = aiSettings.provider
      aiStatus.model = aiSettings.model
      ElMessage.success(res.message || 'AI 连接测试成功')
      if (res.data?.response) {
        ElMessage.info(`AI 响应: ${res.data.response.substring(0, 50)}...`)
      }
    } else {
      aiStatus.connected = false
      ElMessage.error(res.message || '连接失败，请检查 API Key')
    }
  } catch (e: any) {
    aiStatus.connected = false
    ElMessage.error(e.message || '连接失败，请检查 API Key')
  } finally {
    testing.value = false
  }
}'''

if old_test in content:
    content = content.replace(old_test, new_test)
    print('Updated testAIConnection function')
else:
    print('testAIConnection pattern not found, checking...')
    idx = content.find('const testAIConnection')
    if idx > 0:
        print(f'Found at {idx}')
        print(content[idx:idx+400])

# 2. 在 onMounted 中加载 AI 提供商列表
old_mounted = '''onMounted(async () => {
  try {
    const res: any = await systemAPI.getConfig()'''

new_mounted = '''onMounted(async () => {
  try {
    // 加载系统配置
    const res: any = await systemAPI.getConfig()'''

if old_mounted in content:
    content = content.replace(old_mounted, new_mounted)
    print('Updated onMounted')

# 3. 在加载配置后添加加载 AI 状态
old_load_end = '''aiSettings.model = config.ai_model || 'Qwen/Qwen2.5-7B-Instruct'
    }
  } catch (e) {
    console.error('加载配置失败', e)
  }
})'''

new_load_end = '''aiSettings.model = config.ai_model || 'Qwen/Qwen2.5-7B-Instruct'
      // 更新状态显示
      aiStatus.provider = aiSettings.provider
      aiStatus.connected = !!aiSettings.apiKey
    }
    // 加载 AI 提供商列表
    try {
      const providersRes: any = await systemAPI.listAIProviders()
      if (providersRes.data?.current) {
        aiStatus.provider = providersRes.data.current.provider
        aiStatus.connected = providersRes.data.current.configured
        aiStatus.model = providersRes.data.current.model
      }
    } catch (e) {
      console.error('加载AI提供商失败', e)
    }
  } catch (e) {
    console.error('加载配置失败', e)
  }
})'''

if old_load_end in content:
    content = content.replace(old_load_end, new_load_end)
    print('Updated load config end')

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('Done: Settings.vue updated')
