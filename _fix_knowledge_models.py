# -*- coding: utf-8 -*-
"""
修复 Knowledge.vue - 从系统配置加载嵌入和重排模型
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Knowledge.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 修改 loadEmbeddingModels 函数，从配置加载
old_load_embed = '''async function loadEmbeddingModels() {
  try {
    const res: any = await systemAPI.listEmbeddingModels()
    if (res.data?.models) {
      const models = res.data.models
      if (Array.isArray(models)) {
        const stAvailable = !!res.data.st_available
        const apiModels = models.filter((m: any) => m.provider === 'api')
        const localModels = models.filter((m: any) => m.provider === 'local')
        // 修复：后端返回的字段是 name 不是 id
        if (apiModels.length) {
          apiEmbeddingModels.value = apiModels.map((m: any) => ({
            value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`
          }))
        }
        if (localModels.length) {
          localEmbeddingModels.value = localModels.map((m: any) => ({
            value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`, available: stAvailable && m.available
          }))
        }
      }
    }
  } catch (e) {
    console.error('加载嵌入模型列表失败:', e)
    // 使用默认列表
  }
}'''

new_load_embed = '''async function loadEmbeddingModels() {
  try {
    // 优先从系统配置加载已配置的嵌入模型
    const configRes: any = await systemAPI.getConfig()
    if (configRes.data?.embed_models) {
      const models = typeof configRes.data.embed_models === 'string' 
        ? JSON.parse(configRes.data.embed_models) 
        : configRes.data.embed_models
      if (Array.isArray(models) && models.length > 0) {
        apiEmbeddingModels.value = models.map((m: any) => ({
          value: m.modelId, 
          label: m.name || m.modelId, 
          desc: m.provider === 'local' ? '本地模型' : `${m.dimension || 768}维`,
          provider: m.provider
        }))
        console.log('从配置加载嵌入模型:', apiEmbeddingModels.value.length)
        return
      }
    }
    
    // 回退到后端模型列表
    const res: any = await systemAPI.listEmbeddingModels()
    if (res.data?.models) {
      const models = res.data.models
      if (Array.isArray(models)) {
        const stAvailable = !!res.data.st_available
        const apiModels = models.filter((m: any) => m.provider === 'api')
        const localModels = models.filter((m: any) => m.provider === 'local')
        if (apiModels.length) {
          apiEmbeddingModels.value = apiModels.map((m: any) => ({
            value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`
          }))
        }
        if (localModels.length) {
          localEmbeddingModels.value = localModels.map((m: any) => ({
            value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`, available: stAvailable && m.available
          }))
        }
      }
    }
  } catch (e) {
    console.error('加载嵌入模型列表失败:', e)
    // 使用默认列表（已在 ref 中定义）
  }
}'''

if old_load_embed in content:
    content = content.replace(old_load_embed, new_load_embed)
    print("[OK] loadEmbeddingModels 已更新")
else:
    print("[WARN] 未找到 loadEmbeddingModels，尝试其他匹配")

# 2. 修改 loadRerankModels 函数
old_load_rerank = '''async function loadRerankModels() {
  try {
    // 注意：systemAPI 中没有 listRerankModels 方法，使用默认列表
    console.log('使用默认重排模型列表')
  } catch (e) {
    console.error('加载重排模型列表失败:', e)
    // 使用默认列表
  }
}'''

new_load_rerank = '''async function loadRerankModels() {
  try {
    // 从系统配置加载已配置的重排模型
    const configRes: any = await systemAPI.getConfig()
    if (configRes.data?.rerank_models) {
      const models = typeof configRes.data.rerank_models === 'string' 
        ? JSON.parse(configRes.data.rerank_models) 
        : configRes.data.rerank_models
      if (Array.isArray(models) && models.length > 0) {
        rerankModels.value = models.map((m: any) => ({
          value: m.modelId, 
          label: m.name || m.modelId, 
          desc: '重排模型'
        }))
        console.log('从配置加载重排模型:', rerankModels.value.length)
        return
      }
    }
    // 使用默认列表（已在 ref 中定义）
    console.log('使用默认重排模型列表')
  } catch (e) {
    console.error('加载重排模型列表失败:', e)
    // 使用默认列表
  }
}'''

if old_load_rerank in content:
    content = content.replace(old_load_rerank, new_load_rerank)
    print("[OK] loadRerankModels 已更新")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\nKnowledge.vue 修复完成！")