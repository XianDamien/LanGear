import axios from 'axios'
import { ElMessage } from 'element-plus'
import { installMockAdapter } from './mockAdapter'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

if (import.meta.env.VITE_USE_MOCK === 'true') {
  installMockAdapter(http)
} else {
  // Only add error toast for real API calls (mock adapter handles its own flow)
  http.interceptors.response.use(
    (response) => response,
    (error) => {
      const msg =
        error.response?.data?.error?.message ||
        error.message ||
        '网络请求失败'
      ElMessage.error(msg)
      return Promise.reject(error)
    },
  )
}

export default http
