import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import legacy from '@vitejs/plugin-legacy'
import { resolve } from 'path'

export default defineConfig({
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
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue-core': ['vue', 'vue-router', 'pinia']
        }
      }
    }
  },
  optimizeDeps: {
    include: ['element-plus']
  },
  server: {
    port: 5123,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8788',
        changeOrigin: true
      }
    }
  }
})
