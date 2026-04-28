/**
 * 我的应用模块 - API 封装
 */
import request from './index'

// 应用管理
export const appAPI = {
  // 创建应用
  create: (data: { name: string; description?: string; icon?: string; theme?: string }) => 
    request.post('/apps/', data),
  
  // 获取应用列表
  list: () => request.get('/apps/'),
  
  // 获取应用详情
  get: (id: number) => request.get(`/apps/${id}`),
  
  // 更新应用
  update: (id: number, data: Partial<{
    name: string; description: string; icon: string; theme: string;
    is_published: boolean; is_public: boolean;
    knowledge_base_ids: number[]; knowledge_config: Record<string, any>;
    workflow_ids: number[]; workflow_config: Record<string, any>;
    bound_agents: any[];
    dashboard_config: any;
    config: any;
  }>) => request.put(`/apps/${id}`, data),
  
  // 删除应用
  delete: (id: number) => request.delete(`/apps/${id}`),
  
  // 发布应用
  publish: (id: number) => request.post(`/apps/${id}/publish`),

  // 撤回应用（取消发布）
  unpublish: (id: number) => request.post(`/apps/${id}/unpublish`),
  
  // 菜单管理
  addMenu: (appId: number, data: { template_id: number; menu_label: string; menu_icon?: string; menu_order?: number; parent_id?: number }) => 
    request.post(`/apps/${appId}/menus`, data),
  
  updateMenu: (menuId: number, data: Partial<{ menu_label: string; menu_icon: string; menu_order: number; parent_id: number }>) => 
    request.put(`/apps/menus/${menuId}`, data),
  
  deleteMenu: (menuId: number) => request.delete(`/apps/menus/${menuId}`),
  
  getMenuTree: (appId: number) => request.get(`/apps/${appId}/menus/tree`),
  
  // 关系管理
  addRelation: (appId: number, data: { from_template_id: number; from_field_name: string; to_template_id: number; relation_type: string }) => 
    request.post(`/apps/${appId}/relations`, data),
  
  listRelations: (appId: number) => request.get(`/apps/${appId}/relations`),
  
  deleteRelation: (relationId: number) => request.delete(`/apps/relations/${relationId}`),
  
  // 插件管理
  addPlugin: (appId: number, data: { name: string; trigger_event: string; script_code: string; target_template_id?: number }) => 
    request.post(`/apps/${appId}/plugins`, data),
  
  listPlugins: (appId: number) => request.get(`/apps/${appId}/plugins`),
  
  updatePlugin: (pluginId: number, data: Partial<{ name: string; script_code: string; is_enabled: boolean }>) => 
    request.put(`/apps/plugins/${pluginId}`, data),
  
  deletePlugin: (pluginId: number) => request.delete(`/apps/plugins/${pluginId}`),
  
  // ============ 插件管理（独立端点） ============
  getSnippets: () => request.get('/plugins/snippets'),
  listPluginsNew: (appId: number) => request.get(`/plugins/app/${appId}`),
  addPluginNew: (appId: number, data: any) => request.post(`/plugins/app/${appId}`, data),
  getPlugin: (pluginId: number) => request.get(`/plugins/${pluginId}`),
  updatePluginNew: (pluginId: number, data: any) => request.put(`/plugins/${pluginId}`, data),
  deletePluginNew: (pluginId: number) => request.delete(`/plugins/${pluginId}`),
  testPlugin: (pluginId: number, mockData?: any) => request.post(`/plugins/${pluginId}/test`, mockData),
  
  // ============ 仪表盘 ============
  getDashboard: (appId: number) => request.get(`/apps/${appId}/dashboard`),
  saveDashboard: (appId: number, config: any) => request.put(`/apps/${appId}/dashboard`, config),
  getWidgetData: (widgetConfig: any) => request.post('/apps/dashboard/widget/data', widgetConfig),
  getFieldLabels: (templateIds: number[]) =>
    request.get('/apps/field-labels', { params: { ids: templateIds.join(',') } }),
  
  // ============ 权限 ============
  getPermissions: (appId: number) => request.get(`/permissions/app/${appId}`),
  savePermissions: (appId: number, config: any) => request.put(`/permissions/app/${appId}`, config),
  getAuditLogs: (params?: any) => request.get('/permissions/audit-logs', { params }),
  exportAuditLogs: (params?: any) => request.get('/permissions/audit-logs/export', { params }),
  
  // ============ AI设计助手 ============
  // 超时时间 180 秒，因为 AI 生成需要较长时间
  generateAIDesign: (data: { app_id: number; prompt: string }) => 
    request.post('/ai-design/generate', data, { timeout: 180000 }),
  applyAIDesign: (appId: number, design: any) => 
    request.post(`/ai-design/apply/${appId}`, design, { timeout: 180000 }),

  // ============ 版本管理 ============
  listVersions: (appId: number) => request.get(`/apps/${appId}/versions`),
  createVersion: (appId: number, data: { version: string; changelog?: string; is_stable?: boolean }) =>
    request.post(`/apps/${appId}/versions`, data),
  restoreVersion: (appId: number, versionId: number) =>
    request.post(`/apps/${appId}/versions/${versionId}/restore`),

  // ============ AI 应用生成 ============
  // 超时时间 300 秒（5分钟），因为 AI 生成整个应用需要更长时间
  aiGenerate: (description: string, appName?: string, options?: { skipWorkflow?: boolean; skipDashboard?: boolean; skipAgent?: boolean }) =>
    request.post('/apps/ai-generate', null, {
      params: {
        description,
        app_name: appName,
        skip_workflow: options?.skipWorkflow,
        skip_dashboard: options?.skipDashboard,
        skip_agent: options?.skipAgent,
      },
      timeout: 300000,
    }),
}

export default appAPI
