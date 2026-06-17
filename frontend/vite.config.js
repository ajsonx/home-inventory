import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发时把 /api 与 /uploads 代理到 Flask 后端（默认 8000 端口），
// 与后端同源行为保持一致，cookie 鉴权可正常工作。
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/uploads': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    // 构建产物默认输出到 dist，由 Flask 托管
    outDir: 'dist',
  },
})
