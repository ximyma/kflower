/**
 * 模板插件管理 API
 */

// 获取模板绑定的插件列表
export async function getTemplatePlugins(templateId: number) {
  const { default: api } = await import('./index')
  return api.get(`/templates/${templateId}/plugins`)
}

// 获取可绑定到模板的插件列表
export async function getAvailablePlugins(templateId: number, params?: { category?: string; search?: string }) {
  const { default: api } = await import('./index')
  return api.get(`/templates/${templateId}/plugins/available`, { params })
}

// 绑定插件到模板
export async function bindPluginToTemplate(templateId: number, pluginId: number, config?: Record<string, any>) {
  const { default: api } = await import('./index')
  return api.post(`/templates/${templateId}/plugins/bind`, { plugin_id: pluginId, config })
}

// 解除插件与模板的绑定
export async function unbindPlugin(templateId: number, bindingId: number) {
  const { default: api } = await import('./index')
  return api.delete(`/templates/${templateId}/plugins/${bindingId}`)
}

// 更新模板插件绑定配置
export async function updateTemplatePluginBinding(
  templateId: number,
  bindingId: number,
  data: { is_enabled?: boolean; config?: Record<string, any>; sort_order?: number }
) {
  const { default: api } = await import('./index')
  return api.put(`/templates/${templateId}/plugins/${bindingId}`, data)
}

// 手动触发模板插件钩子（测试用）
export async function triggerTemplatePluginHook(templateId: number, hookName: string, context: Record<string, any>) {
  const { default: api } = await import('./index')
  return api.post(`/templates/${templateId}/plugins/trigger`, { hook_name: hookName, context })
}
