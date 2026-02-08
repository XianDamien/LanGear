import type { AxiosInstance } from 'axios'
import { mockDashboardData } from './mock/dashboard'
import { mockDeckTree, mockLessonCards } from './mock/decks'
import { mockSubmitReview } from './mock/study'
import { mockLessonSummary } from './mock/summary'
import { mockSettings } from './mock/settings'
import type { SettingsData } from '@/types/api'

function delay(ms = 400): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

interface MockResponse {
  __mock: true
  data?: unknown
  error?: { code: string; message: string; request_id: string }
  status?: number
}

function mockResolve(data: unknown): MockResponse {
  return { __mock: true, data }
}

function mockError(code: string, message: string, status = 404): MockResponse {
  return { __mock: true, error: { code, message, request_id: 'mock' }, status }
}

export function installMockAdapter(http: AxiosInstance) {
  http.interceptors.request.use(async (config) => {
    const url = config.url || ''
    const method = (config.method || 'get').toLowerCase()

    let mock: MockResponse | null = null

    // GET /dashboard
    if (method === 'get' && url === '/dashboard') {
      await delay()
      mock = mockResolve(mockDashboardData)
    }

    // GET /decks/tree
    if (!mock && method === 'get' && url === '/decks/tree') {
      await delay()
      mock = mockResolve(mockDeckTree)
    }

    // GET /decks/:lessonId/cards
    if (!mock) {
      const cardsMatch = url.match(/^\/decks\/([^/]+)\/cards$/)
      if (method === 'get' && cardsMatch) {
        await delay()
        const lessonId = cardsMatch[1]!
        const data = mockLessonCards[lessonId]
        mock = data
          ? mockResolve(data)
          : mockError('NOT_FOUND', '课程不存在')
      }
    }

    // POST /study/submissions
    if (!mock && method === 'post' && url === '/study/submissions') {
      await delay(800)
      const body = typeof config.data === 'string' ? JSON.parse(config.data) : config.data
      const data = mockSubmitReview(String(body?.cardId ?? ''), '')
      mock = mockResolve(data)
    }

    // GET /decks/:lessonId/summary
    if (!mock) {
      const summaryMatch = url.match(/^\/decks\/([^/]+)\/summary$/)
      if (method === 'get' && summaryMatch) {
        await delay(600)
        mock = mockResolve(mockLessonSummary(summaryMatch[1]!))
      }
    }

    // GET /settings
    if (!mock && method === 'get' && url === '/settings') {
      await delay()
      mock = mockResolve({ ...mockSettings })
    }

    // PUT /settings
    if (!mock && method === 'put' && url === '/settings') {
      await delay()
      const body = typeof config.data === 'string' ? JSON.parse(config.data) : config.data
      mock = mockResolve(body as SettingsData)
    }

    if (mock) {
      return Promise.reject(mock)
    }
    return config
  })

  // Intercept mock rejections and convert to resolved responses
  http.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error?.__mock) {
        if (error.error) {
          return Promise.reject({
            response: { data: { error: error.error }, status: error.status || 500 },
          })
        }
        return Promise.resolve({ data: error.data, status: 200 })
      }
      return Promise.reject(error)
    },
  )
}
