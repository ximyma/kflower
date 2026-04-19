/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '../store/user'

// 路由配置
const routes: RouteRecordRaw[] = [
  // 公共路由
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
        path: 'my-apps',
        name: 'MyApps',
        component: () => import('../../pc/views/MyApps.vue'),
        meta: { title: '我的应用' }
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
        path: 'migration',
        name: 'Migration',
        component: () => import('../../pc/views/Migration.vue'),
        meta: { title: '数据迁移' }
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

  // 移动端路由
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
        path: 'work',
        name: 'AppWork',
        component: () => import('../../app/views/Work.vue'),
        meta: { title: '工作' }
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

  // 需要认证
  if (requiresAuth && !userStore.isLoggedIn) {
    // 尝试自动登录（token存在但页面刷新后userInfo丢失）
    if (localStorage.getItem('kflower_token')) {
      const loggedIn = await userStore.autoLogin()
      if (!loggedIn) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    } else {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }

  // 检查管理员权限
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    // 非管理员访问需要管理员权限的页面，重定向到首页
    next({ name: 'Home' })
    return
  }

  // 已登录访问登录页
  if (to.name === 'Login' && userStore.isLoggedIn) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router
