import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页', keepAlive: true }
  },
  {
    path: '/apps',
    name: 'Apps',
    component: () => import('../views/Work.vue'),
    meta: { title: '应用' }
  },
  {
    path: '/todo',
    name: 'Todo',
    component: () => import('../views/Home.vue'),
    meta: { title: '待办' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '我的' }
  },
  {
    path: '/workflow/:id',
    name: 'WorkflowDetail',
    component: () => import('../views/Work.vue'),
    meta: { title: '工作流详情' }
  },
  {
    path: '/workflow/new',
    name: 'NewWorkflow',
    component: () => import('../views/Work.vue'),
    meta: { title: '新建工作流' }
  },
  {
    path: '/templates',
    name: 'Templates',
    component: () => import('../views/Work.vue'),
    meta: { title: '模板' }
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('../views/Home.vue'),
    meta: { title: '数据分析' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Profile.vue'),
    meta: { title: '设置' }
  },
  {
    path: '/ai-settings',
    name: 'AISettings',
    component: () => import('../views/Profile.vue'),
    meta: { title: 'AI配置' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (!token && to.path !== '/login') {
    next('/login')
  } else {
    next()
  }
})

export default router