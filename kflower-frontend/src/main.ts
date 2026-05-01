// @ts-nocheck
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './common/router'
import { checkDevice } from './common/utils/device'

import './common/styles/index.scss'

// 设备检测
const isMobile = checkDevice()
console.log(`[Kflower] Device: ${isMobile ? 'Mobile' : 'PC'}`)

// 创建Vue应用
const app = createApp(App)

// 注册Pinia状态管理
app.use(createPinia())

// 注册路由
app.use(router)

// 注册Element Plus
app.use(ElementPlus, { locale: zhCn })

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 挂载应用
app.mount('#app')
