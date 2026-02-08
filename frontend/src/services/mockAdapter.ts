import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
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

function parseBody(config: InternalAxiosRequestConfig): unknown {
  return typeof config.data === 'string' ? JSON.parse(config.data) : config.data
}

async function matchRoute(config: InternalAxiosRequestConfig): Promise<MockResponse | null> {
  const url = config.url || ''
  const method = (config.method || 'get').toLowerCase()

  if (method === 'get' && url === '/dashboard') {
    await delay()
    return mockResolve(mockDashboardData)
  }

  if (method === 'get' && url === '/decks/tree') {
    await delay()
    return mockResolve(mockDeckTree)
  }

  const cardsMatch = url.match(/^\/decks\/([^/]+)\/cards$/)
  if (method === 'get' && cardsMatch) {
    await delay()
    const data = mockLessonCards[cardsMatch[1]!]
    return data ? mockResolve(data) : mockError('NOT_FOUND', '课程不存在')
  }

  if (method === 'post' && url === '/study/submissions') {
    await delay(800)
    const body = parseBody(config) as { cardId?: unknown }
    return mockResolve(mockSubmitReview(String(body?.cardId ?? ''), ''))
  }

  const summaryMatch = url.match(/^\/decks\/([^/]+)\/summary$/)
  if (method === 'get' && summaryMatch) {
    await delay(600)
    return mockResolve(mockLessonSummary(summaryMatch[1]!))
  }

  if (method === 'get' && url === '/settings') {
    await delay()
    return mockResolve({ ...mockSettings })
  }

  if (method === 'put' && url === '/settings') {
    await delay()
    return mockResolve(parseBody(config) as SettingsData)
  }

  return null
}

export function installMockAdapter(http: AxiosInstance) {
  http.interceptors.request.use(async (config) => {
    const mock = await matchRoute(config)
    if (mock) return Promise.reject(mock)
    return config
  })

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
