// vite.config.ts
import { defineConfig } from "file:///D:/kkflower/kflower-frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///D:/kkflower/kflower-frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import legacy from "file:///D:/kkflower/kflower-frontend/node_modules/@vitejs/plugin-legacy/dist/index.mjs";
import externalGlobals from "file:///D:/kkflower/kflower-frontend/node_modules/rollup-plugin-external-globals/index.js";
import { resolve } from "path";
var __vite_injected_original_dirname = "D:\\kkflower\\kflower-frontend";
var cdnGlobals = {
  vue: "Vue",
  "vue-router": "VueRouter",
  pinia: "Pinia",
  "element-plus": "ElementPlus",
  "@element-plus/icons-vue": "ElementPlusIconsVue",
  echarts: "echarts",
  axios: "axios",
  xlsx: "XLSX"
};
var vite_config_default = defineConfig(({ mode }) => {
  const isProduction = mode === "production";
  return {
    plugins: [
      vue(),
      legacy({
        targets: ["defaults", "not IE 11", "chrome 100"],
        additionalLegacyPolyfills: ["regenerator-runtime/runtime"],
        polyfills: false
      })
    ],
    resolve: {
      alias: {
        "@": resolve(__vite_injected_original_dirname, "src")
      }
    },
    esbuild: {
      target: "es2020"
    },
    build: {
      target: ["es2020", "chrome100"],
      cssTarget: "chrome100",
      rollupOptions: {
        // 生产构建时使用 external-globals 插件
        plugins: isProduction ? [
          externalGlobals(cdnGlobals)
        ] : []
      },
      chunkSizeWarningLimit: 1e3
    },
    optimizeDeps: {
      include: ["element-plus", "echarts", "@element-plus/icons-vue"]
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8788",
          changeOrigin: true
        }
      }
    }
  };
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJEOlxcXFxra2Zsb3dlclxcXFxrZmxvd2VyLWZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJEOlxcXFxra2Zsb3dlclxcXFxrZmxvd2VyLWZyb250ZW5kXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9EOi9ra2Zsb3dlci9rZmxvd2VyLWZyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcclxuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXHJcbmltcG9ydCBsZWdhY3kgZnJvbSAnQHZpdGVqcy9wbHVnaW4tbGVnYWN5J1xyXG5pbXBvcnQgZXh0ZXJuYWxHbG9iYWxzIGZyb20gJ3JvbGx1cC1wbHVnaW4tZXh0ZXJuYWwtZ2xvYmFscydcclxuaW1wb3J0IHsgcmVzb2x2ZSB9IGZyb20gJ3BhdGgnXHJcblxyXG4vLyBDRE4gXHU1MTY4XHU1QzQwXHU1M0Q4XHU5MUNGXHU2NjIwXHU1QzA0XHJcbmNvbnN0IGNkbkdsb2JhbHMgPSB7XHJcbiAgdnVlOiAnVnVlJyxcclxuICAndnVlLXJvdXRlcic6ICdWdWVSb3V0ZXInLFxyXG4gIHBpbmlhOiAnUGluaWEnLFxyXG4gICdlbGVtZW50LXBsdXMnOiAnRWxlbWVudFBsdXMnLFxyXG4gICdAZWxlbWVudC1wbHVzL2ljb25zLXZ1ZSc6ICdFbGVtZW50UGx1c0ljb25zVnVlJyxcclxuICBlY2hhcnRzOiAnZWNoYXJ0cycsXHJcbiAgYXhpb3M6ICdheGlvcycsXHJcbiAgeGxzeDogJ1hMU1gnXHJcbn1cclxuXHJcbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZygoeyBtb2RlIH0pID0+IHtcclxuICBjb25zdCBpc1Byb2R1Y3Rpb24gPSBtb2RlID09PSAncHJvZHVjdGlvbidcclxuICBcclxuICByZXR1cm4ge1xyXG4gICAgcGx1Z2luczogW1xyXG4gICAgICB2dWUoKSxcclxuICAgICAgbGVnYWN5KHtcclxuICAgICAgICB0YXJnZXRzOiBbJ2RlZmF1bHRzJywgJ25vdCBJRSAxMScsICdjaHJvbWUgMTAwJ10sXHJcbiAgICAgICAgYWRkaXRpb25hbExlZ2FjeVBvbHlmaWxsczogWydyZWdlbmVyYXRvci1ydW50aW1lL3J1bnRpbWUnXSxcclxuICAgICAgICBwb2x5ZmlsbHM6IGZhbHNlXHJcbiAgICAgIH0pXHJcbiAgICBdLFxyXG4gICAgcmVzb2x2ZToge1xyXG4gICAgICBhbGlhczoge1xyXG4gICAgICAgICdAJzogcmVzb2x2ZShfX2Rpcm5hbWUsICdzcmMnKVxyXG4gICAgICB9XHJcbiAgICB9LFxyXG4gICAgZXNidWlsZDoge1xyXG4gICAgICB0YXJnZXQ6ICdlczIwMjAnXHJcbiAgICB9LFxyXG4gICAgYnVpbGQ6IHtcclxuICAgICAgdGFyZ2V0OiBbJ2VzMjAyMCcsICdjaHJvbWUxMDAnXSxcclxuICAgICAgY3NzVGFyZ2V0OiAnY2hyb21lMTAwJyxcclxuICAgICAgcm9sbHVwT3B0aW9uczoge1xyXG4gICAgICAgIC8vIFx1NzUxRlx1NEVBN1x1Njc4NFx1NUVGQVx1NjVGNlx1NEY3Rlx1NzUyOCBleHRlcm5hbC1nbG9iYWxzIFx1NjNEMlx1NEVGNlxyXG4gICAgICAgIHBsdWdpbnM6IGlzUHJvZHVjdGlvbiA/IFtcclxuICAgICAgICAgIGV4dGVybmFsR2xvYmFscyhjZG5HbG9iYWxzKVxyXG4gICAgICAgIF0gOiBbXVxyXG4gICAgICB9LFxyXG4gICAgICBjaHVua1NpemVXYXJuaW5nTGltaXQ6IDEwMDBcclxuICAgIH0sXHJcbiAgICBvcHRpbWl6ZURlcHM6IHtcclxuICAgICAgaW5jbHVkZTogWydlbGVtZW50LXBsdXMnLCAnZWNoYXJ0cycsICdAZWxlbWVudC1wbHVzL2ljb25zLXZ1ZSddXHJcbiAgICB9LFxyXG4gICAgc2VydmVyOiB7XHJcbiAgICAgIHBvcnQ6IDUxNzMsXHJcbiAgICAgIHByb3h5OiB7XHJcbiAgICAgICAgJy9hcGknOiB7XHJcbiAgICAgICAgICB0YXJnZXQ6ICdodHRwOi8vMTI3LjAuMC4xOjg3ODgnLFxyXG4gICAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlXHJcbiAgICAgICAgfVxyXG4gICAgICB9XHJcbiAgICB9XHJcbiAgfVxyXG59KVxyXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQTRRLFNBQVMsb0JBQW9CO0FBQ3pTLE9BQU8sU0FBUztBQUNoQixPQUFPLFlBQVk7QUFDbkIsT0FBTyxxQkFBcUI7QUFDNUIsU0FBUyxlQUFlO0FBSnhCLElBQU0sbUNBQW1DO0FBT3pDLElBQU0sYUFBYTtBQUFBLEVBQ2pCLEtBQUs7QUFBQSxFQUNMLGNBQWM7QUFBQSxFQUNkLE9BQU87QUFBQSxFQUNQLGdCQUFnQjtBQUFBLEVBQ2hCLDJCQUEyQjtBQUFBLEVBQzNCLFNBQVM7QUFBQSxFQUNULE9BQU87QUFBQSxFQUNQLE1BQU07QUFDUjtBQUVBLElBQU8sc0JBQVEsYUFBYSxDQUFDLEVBQUUsS0FBSyxNQUFNO0FBQ3hDLFFBQU0sZUFBZSxTQUFTO0FBRTlCLFNBQU87QUFBQSxJQUNMLFNBQVM7QUFBQSxNQUNQLElBQUk7QUFBQSxNQUNKLE9BQU87QUFBQSxRQUNMLFNBQVMsQ0FBQyxZQUFZLGFBQWEsWUFBWTtBQUFBLFFBQy9DLDJCQUEyQixDQUFDLDZCQUE2QjtBQUFBLFFBQ3pELFdBQVc7QUFBQSxNQUNiLENBQUM7QUFBQSxJQUNIO0FBQUEsSUFDQSxTQUFTO0FBQUEsTUFDUCxPQUFPO0FBQUEsUUFDTCxLQUFLLFFBQVEsa0NBQVcsS0FBSztBQUFBLE1BQy9CO0FBQUEsSUFDRjtBQUFBLElBQ0EsU0FBUztBQUFBLE1BQ1AsUUFBUTtBQUFBLElBQ1Y7QUFBQSxJQUNBLE9BQU87QUFBQSxNQUNMLFFBQVEsQ0FBQyxVQUFVLFdBQVc7QUFBQSxNQUM5QixXQUFXO0FBQUEsTUFDWCxlQUFlO0FBQUE7QUFBQSxRQUViLFNBQVMsZUFBZTtBQUFBLFVBQ3RCLGdCQUFnQixVQUFVO0FBQUEsUUFDNUIsSUFBSSxDQUFDO0FBQUEsTUFDUDtBQUFBLE1BQ0EsdUJBQXVCO0FBQUEsSUFDekI7QUFBQSxJQUNBLGNBQWM7QUFBQSxNQUNaLFNBQVMsQ0FBQyxnQkFBZ0IsV0FBVyx5QkFBeUI7QUFBQSxJQUNoRTtBQUFBLElBQ0EsUUFBUTtBQUFBLE1BQ04sTUFBTTtBQUFBLE1BQ04sT0FBTztBQUFBLFFBQ0wsUUFBUTtBQUFBLFVBQ04sUUFBUTtBQUFBLFVBQ1IsY0FBYztBQUFBLFFBQ2hCO0FBQUEsTUFDRjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
