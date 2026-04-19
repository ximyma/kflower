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
  update: (id: number, data: Partial<{ name: string; description: string; icon: string; theme: string; is_published: boolean; is_public: boolean }>) => 
    request.put(`/apps/${id}`, data),
  
  // 删除应用
  delete: (id: number) => request.delete(`/apps/${id}`),
  
  // 发布应用
  publish: (id: number) => request.post(`/apps/${id}/publish`),
  
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
}

export default appAPI
