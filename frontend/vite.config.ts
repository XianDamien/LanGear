import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, '')
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3002,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          ws: true,
        },
      },
    },
  }
})
