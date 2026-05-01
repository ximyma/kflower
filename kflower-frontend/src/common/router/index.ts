/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '../store/user'
import { checkDevice } from '../utils/device'

// 路由配置
const routes: RouteRecordRaw[] = [
  // 公共路由（PC端）
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },

  // 公共路由（移动端）
  {
    path: '/app/login',
    name: 'AppLogin',
    component: () => import('../mobile/views/Login.vue'),
    meta: { requiresAuth: false, layout: 'mobile' }
  },
  {
    path: '/app/register',
    name: 'AppRegister',
    component: () => import('../mobile/views/Register.vue'),
    meta: { requiresAuth: false, layout: 'mobile' }
  },

  // PC端路由
  {
    path: '/',
    component: () => import('../../pc/layouts/MainLayout.vue'),
    meta: { requiresAuth: true, layout: 'pc' },
    children: [
      {
        path: '',
        redirect: '/home'
      },
      {
        path: 'home',
        name: 'Home',
        component: () => import('../../pc/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('../../pc/views/UserProfile.vue'),
        meta: { title: '个人信息' }
      },
      {
        path: 'my-workspace',
        name: 'MyWorkspace',
        component: () => import('../../pc/views/MyWorkspace.vue'),
        meta: { title: '我的工作区' }
      },
      {
        path: 'templates',
        name: 'Templates',
        component: () => import('../../pc/views/Templates.vue'),
        meta: { title: '模板设计' }
      },
      {
        path: 'workflows',
        name: 'Workflows',
        component: () => import('../../pc/views/Workflows.vue'),
        meta: { title: '流程审批' }
      },
      {
        path: 'workflows/design/:id?',
        name: 'WorkflowDesigner',
        component: () => import('../../pc/views/WorkflowDesigner.vue'),
        meta: { title: '流程设计', hideInMenu: true }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('../../pc/views/Analytics.vue'),
        meta: { title: '决策分析' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../../pc/views/Knowledge.vue'),
        meta: { title: '知识库' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../../pc/views/Settings.vue'),
        meta: { title: '系统设置' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../../pc/views/Users.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      },
      
      {
        path: 'ai-digital-base',
        name: 'AIDigitalBase',
        component: () => import('../../pc/views/AIDigitalBase.vue'),
        meta: { title: 'AI数字底座' }
      },
      {
        path: 'ai-agent-engine',
        name: 'AIAgentEngine',
        component: () => import('../../pc/views/AIAgentEngine.vue'),
        meta: { title: 'AI智能体引擎' }
      },
      {
        path: 'ai-gateway',
        name: 'AIGateway',
        component: () => import('../../pc/views/AIGateway.vue'),
        meta: { title: 'AI网关' }
      },
      {
        path: 'ai-tools',
        name: 'AITools',
        component: () => import('../../pc/views/AITools.vue'),
        meta: { title: '工具集' }
      },
      {
        path: 'agent-orchestrator',
        name: 'AgentOrchestrator',
        component: () => import('../../pc/views/AgentOrchestrator.vue'),
        meta: { title: '智能体编排器' }
      },
      {
        path: 'memory-management',
        name: 'MemoryManagement',
        component: () => import('../../pc/views/MemoryManagement.vue'),
        meta: { title: '记忆管理' }
      },
      {
        path: 'data-integration',
        name: 'DataIntegration',
        component: () => import('../../pc/views/DataIntegration.vue'),
        meta: { title: '数据集成' }
      },
      {
        path: 'my-apps',
        name: 'MyApps',
        component: () => import('../../pc/views/MyApps.vue'),
        meta: { title: '我的应用' }
      },
      {
        path: 'app-data-view',
        name: 'AppDataView',
        component: () => import('../../pc/views/AppDataView.vue'),
        meta: { title: '应用数据视图' }
      },
      {
        path: 'ai-app-designer',
        name: 'AIAppDesigner',
        component: () => import('../../pc/views/my-apps/AIAppDesigner.vue'),
        meta: { title: 'AI设计助手', hideInMenu: true }
      },
      {
        path: 'app-designer/:appId',
        name: 'AppDesigner',
        component: () => import('../../pc/views/my-apps/AppDesigner.vue'),
        meta: { title: '应用设计', hideInMenu: true }
      },
      {
        path: 'data-modeling',
        name: 'DataModeling',
        component: () => import('../../pc/views/DataModeling.vue'),
        meta: { title: '数据建模' }
      },
      {
        path: 'plugins',
        name: 'PluginManager',
        component: () => import('../../pc/views/PluginManager.vue'),
        meta: { title: '插件管理' }
      },
      {
        path: 'plugin-designer/:id?',
        name: 'PluginDesigner',
        component: () => import('../../pc/views/PluginDesigner.vue'),
        meta: { title: '插件设计器', hideInMenu: true }
      },
      {
        path: 'plugin-market',
        name: 'PluginMarket',
        component: () => import('../../pc/views/PluginMarket.vue'),
        meta: { title: '插件市场' }
      },
      {
        path: 'data-modeling/designer/:id?',
        name: 'DataModelDesigner',
        component: () => import('../../pc/views/DataModelDesigner.vue'),
        meta: { title: '模型设计', hideInMenu: true }
      },
      {
        path: 'data-modeling/import',
        name: 'DataModelImport',
        component: () => import('../../pc/views/DataModelImport.vue'),
        meta: { title: '导入数据表', hideInMenu: true }
      },
      {
        path: 'migration',
        name: 'Migration',
        component: () => import('../../pc/views/Migration.vue'),
        meta: { title: '数据迁移' }
      },
      {
        path: 'doc-converter',
        name: 'DocConverter',
        component: () => import('../../pc/views/DocConverter.vue'),
        meta: { title: '文档转换' }
      },
      {
        path: 'form/:id',
        name: 'FormFill',
        component: () => import('../../pc/views/FormFill.vue'),
        meta: { title: '表单填写' }
      },
      {
        path: 'form/:id/data',
        name: 'FormData',
        component: () => import('../../pc/views/FormData.vue'),
        meta: { title: '数据管理' }
      }
    ]
  },

  // 应用容器路由
  {
    path: '/app/:appId',
    component: () => import('../../pc/views/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'AppDashboard',
        component: () => import('../../pc/views/my-apps/AppDashboard.vue'),
        meta: { title: '应用首页' }
      },
      {
        path: 'form/:templateId',
        name: 'AppFormList',
        component: () => import('../../pc/views/FormListPage.vue'),
        meta: { title: '数据列表' }
      },
      {
        path: 'form/:templateId/edit',
        name: 'AppFormEdit',
        component: () => import('../../pc/views/FormEditPage.vue'),
        meta: { title: '新增数据', hideInMenu: true }
      },
      {
        path: 'form/:templateId/edit/:dataId',
        name: 'AppFormEditDetail',
        component: () => import('../../pc/views/FormEditPage.vue'),
        meta: { title: '编辑数据', hideInMenu: true }
      }
    ]
  },

  // 移动端路由（已登录后的布局）
  {
    path: '/app',
    component: () => import('../../app/layouts/AppLayout.vue'),
    meta: { requiresAuth: true, layout: 'mobile' },
    children: [
      {
        path: '',
        redirect: '/app/home'
      },
      {
        path: 'home',
        name: 'AppHome',
        component: () => import('../../app/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'templates',
        name: 'AppTemplates',
        component: () => import('../../app/views/Templates.vue'),
        meta: { title: '模板设计' }
      },
      {
        path: 'template-designer/:id?',
        name: 'AppTemplateDesigner',
        component: () => import('../../app/views/TemplateDesigner.vue'),
        meta: { title: '模板设计器', hideInTabbar: true }
      },
      {
        path: 'workflows',
        name: 'AppWorkflows',
        component: () => import('../../app/views/Workflows.vue'),
        meta: { title: '流程审批' }
      },
      {
        path: 'workflow-designer/:id?',
        name: 'AppWorkflowDesigner',
        component: () => import('../../app/views/WorkflowDesigner.vue'),
        meta: { title: '流程设计', hideInTabbar: true }
      },
      {
        path: 'knowledge',
        name: 'AppKnowledge',
        component: () => import('../../app/views/Knowledge.vue'),
        meta: { title: '知识库' }
      },
      {
        path: 'workspace',
        name: 'AppWorkspace',
        component: () => import('../../app/views/Workspace.vue'),
        meta: { title: '工作区' }
      },
      {
        path: 'my-apps',
        name: 'AppMyApps',
        component: () => import('../../app/views/MyApps.vue'),
        meta: { title: '我的应用' }
      },
      {
        path: 'app-designer/:appId?',
        name: 'AppAppDesigner',
        component: () => import('../../app/views/AppDesigner.vue'),
        meta: { title: '应用设计', hideInTabbar: true }
      },
      {
        path: 'agents',
        name: 'AppAgents',
        component: () => import('../../app/views/Agents.vue'),
        meta: { title: '我的智能体' }
      },
      {
        path: 'ai-base',
        name: 'AppAIBase',
        component: () => import('../../app/views/AIBase.vue'),
        meta: { title: 'AI数字底座' }
      },
      {
        path: 'ai-tools',
        name: 'AppAITools',
        component: () => import('../../app/views/AITools.vue'),
        meta: { title: 'AI工具集' }
      },
      {
        path: 'chat',
        name: 'AppChat',
        component: () => import('../../app/views/Chat.vue'),
        meta: { title: 'AI助手' }
      },
      {
        path: 'profile',
        name: 'AppProfile',
        component: () => import('../../app/views/Profile.vue'),
        meta: { title: '我的' }
      }
    ]
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
]

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  const isMobile = checkDevice()

  // ===== 设备检测与重定向 =====
  const toPath = to.path
  // 通过路由 meta.layout 判断是否为移动端路由，而非简单的前缀匹配
  // 避免将 /app/:appId（PC应用容器）和 /app-designer/:appId（PC应用设计器）误判为移动端路由
  const isMobileRoute = to.matched.some(r => r.meta.layout === 'mobile')
  const isPublicRoute = ['/login', '/register', '/app/login', '/app/register'].includes(toPath)
  const isRootRoute = toPath === '/'

  // DEBUG
  console.log('[Router]', toPath, { requiresAuth, isMobile, isMobileRoute, isPublicRoute, isRootRoute, isLoggedIn: userStore.isLoggedIn })

  // 手机访问PC端根路径，跳转到手机版登录
  if (isMobile && (isRootRoute || (!isMobileRoute && !isPublicRoute))) {
    console.log('[Router] → redirect to /app/login (mobile guard)')
    next('/app/login')
    return
  }

  // PC访问手机端路径，跳转到PC首页
  if (!isMobile && isMobileRoute && !isPublicRoute) {
    console.log('[Router] → redirect to /home (PC->mobile guard)')
    next('/home')
    return
  }

  // ===== 认证检查 =====
  // 需要认证
  if (requiresAuth && !userStore.isLoggedIn) {
    // 尝试自动登录（token存在但页面刷新后userInfo丢失）
    if (localStorage.getItem('access_token')) {
      const loggedIn = await userStore.autoLogin()
      if (!loggedIn) {
        // 根据设备类型跳转到对应登录页
        const loginPath = isMobile ? '/app/login' : '/login'
        console.log('[Router] → redirect to', loginPath, '(autoLogin failed)')
        next({ path: loginPath, query: { redirect: to.fullPath } })
        return
      }
    } else {
      const loginPath = isMobile ? '/app/login' : '/login'
      console.log('[Router] → redirect to', loginPath, '(no token)')
      next({ path: loginPath, query: { redirect: to.fullPath } })
      return
    }
  }

  // 检查管理员权限
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    // 非管理员访问需要管理员权限的页面，重定向到首页
    console.log('[Router] → redirect to Home (no admin)')
    next({ name: 'Home' })
    return
  }

  // 已登录访问登录页，根据设备类型重定向
  if ((to.name === 'Login' || to.name === 'AppLogin') && userStore.isLoggedIn) {
    const homePath = isMobile ? '/app/home' : '/home'
    console.log('[Router] → redirect to', homePath, '(already logged in, visiting login)')
    next(homePath)
    return
  }

  // 已登录用户访问根路径，根据设备类型跳转
  if (isRootRoute && userStore.isLoggedIn) {
    const homePath = isMobile ? '/app/home' : '/home'
    console.log('[Router] → redirect to', homePath, '(root route)')
    next(homePath)
    return
  }

  console.log('[Router] → allow', toPath)
  next()
})

export default router
