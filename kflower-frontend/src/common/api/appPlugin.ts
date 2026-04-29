/**
 * 应用插件管理 API
 */

// 获取应用的新版插件绑定列表
export async function getAppPlugins(appId: number) {
  const { default: api } = await import('./index')
  return api.get(`/apps/${appId}/plugins/bindings`)
}

// 获取可绑定到应用的插件列表
export async function getAvailablePluginsForApp(appId: number, params?: { category?: string; search?: string }) {
  const { default: api } = await import('./index')
  return api.get(`/apps/${appId}/plugins/available`, { params })
}

// 绑定插件到应用
export async function bindPluginToApp(appId: number, pluginId: number, config?: Record<string, any>) {
  const { default: api } = await import('./index')
  return api.post(`/apps/${appId}/plugins/bind`, { plugin_id: pluginId, config })
}

// 解除插件与应用的绑定
export async function unbindAppPlugin(appId: number, bindingId: number) {
  const { default: api } = await import('./index')
  return api.delete(`/apps/${appId}/plugins/${bindingId}`)
}

// 更新应用插件绑定配置
export async function updateAppPluginBinding(
  appId: number,
  bindingId: number,
  data: { is_enabled?: boolean; config?: Record<string, any>; sort_order?: number }
) {
  const { default: api } = await import('./index')
  return api.put(`/apps/${appId}/plugins/${bindingId}`, data)
}

// 手动触发应用插件钩子（测试用）
export async function triggerAppPluginHook(appId: number, hookName: string, context: Record<string, any>) {
  const { default: api } = await import('./index')
  return api.post(`/apps/${appId}/plugins/trigger`, { hook_name: hookName, context })
}
