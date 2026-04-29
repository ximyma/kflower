import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import legacy from '@vitejs/plugin-legacy'
import externalGlobals from 'rollup-plugin-external-globals'
import { resolve } from 'path'

// CDN 全局变量映射
const cdnGlobals = {
  vue: 'Vue',
  'vue-router': 'VueRouter',
  pinia: 'Pinia',
  'element-plus': 'ElementPlus',
  '@element-plus/icons-vue': 'ElementPlusIconsVue',
  echarts: 'echarts',
  axios: 'axios',
  xlsx: 'XLSX'
}

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  
  return {
    plugins: [
      vue(),
      legacy({
        targets: ['defaults', 'not IE 11', 'chrome 100'],
        additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
        polyfills: false
      })
    ],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    esbuild: {
      target: 'es2020'
    },
    build: {
      target: ['es2020', 'chrome100'],
      cssTarget: 'chrome100',
      rollupOptions: {
        // 生产构建时使用 external-globals 插件
        plugins: isProduction ? [
          externalGlobals(cdnGlobals)
        ] : []
      },
      chunkSizeWarningLimit: 1000
    },
    optimizeDeps: {
      include: ['element-plus', 'echarts', '@element-plus/icons-vue']
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8788',
          changeOrigin: true
        }
      }
    }
  }
})
