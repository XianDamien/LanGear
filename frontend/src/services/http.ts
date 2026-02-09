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
  // Unwrap backend { request_id, data } envelope → return inner data
  http.interceptors.response.use(
    (response) => {
      if (response.data && 'request_id' in response.data && 'data' in response.data) {
        response.data = response.data.data
      }
      return response
    },
    (error) => {
      const msg =
        error.response?.data?.detail?.error?.message ||
        error.response?.data?.error?.message ||
        error.message ||
        '网络请求失败'
      ElMessage.error(msg)
      return Promise.reject(error)
    },
  )
}

export default http
