import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { mockDashboardData } from './mock/dashboard'
import { mockDeckTree, mockLessonCards } from './mock/decks'
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

  // v2.0: GET /oss/sts-token
  if (method === 'get' && url === '/oss/sts-token') {
    await delay()
    return mockResolve({
      access_key_id: 'STS.mock123',
      access_key_secret: 'mock-secret',
      security_token: 'mock-token',
      expiration: new Date(Date.now() + 3600000).toISOString(),
      bucket: 'langear',
      region: 'oss-cn-shanghai'
    })
  }

  // v2.0: POST /study/submissions（异步版本）
  if (method === 'post' && url === '/study/submissions') {
    await delay(200)
    const body = parseBody(config) as {
      realtime_session_id?: string
      transcription_text?: string
    }
    if (!body?.realtime_session_id) {
      return mockError('REALTIME_SESSION_NOT_FOUND', 'Missing realtime_session_id', 400)
    }

    const submissionId = Math.floor(Math.random() * 10000)
    sessionStorage.setItem(
      `submission_${submissionId}`,
      JSON.stringify({
        status: 'processing',
        timestamp: Date.now(),
        realtime_session_id: body.realtime_session_id,
        transcription_text:
          typeof body.transcription_text === 'string' ? body.transcription_text.trim() : '',
      })
    )
    return mockResolve({
      submission_id: submissionId,
      status: 'processing'
    })
  }

  // v2.0: GET /study/submissions/{id}
  const pollMatch = url.match(/^\/study\/submissions\/(\d+)$/)
  if (method === 'get' && pollMatch) {
    await delay(500)
    const submissionId = pollMatch[1]
    const stored = sessionStorage.getItem(`submission_${submissionId}`)

    if (!stored) {
      return mockError('NOT_FOUND', 'Submission not found', 404)
    }

    const data = JSON.parse(stored)
    const elapsed = Date.now() - data.timestamp

    // 模拟3秒处理时间
    if (elapsed < 3000) {
      return mockResolve({
        submission_id: Number(submissionId),
        status: 'processing',
        progress: elapsed < 1500 ? 'asr_completed' : 'ai_processing'
      })
    } else {
      const transcriptText =
        typeof data.transcription_text === 'string' ? data.transcription_text.trim() : ''

      sessionStorage.removeItem(`submission_${submissionId}`)
      return mockResolve({
        submission_id: Number(submissionId),
        status: 'completed',
        result_type: 'single',
        realtime_session_id: data.realtime_session_id,
        transcription: {
          text: transcriptText,
          timestamps: []
        },
        feedback: {
          pronunciation: '发音整体清晰，注意连读部分。',
          completeness: '内容完整，未遗漏关键信息。',
          fluency: '语速适中，部分句末有停顿。',
          suggestions: [
            {
              text: '注意 "the" 在元音前的发音变化',
              target_word: 'the',
              timestamp: 0.4
            },
            {
              text: '尝试更自然的语调起伏'
            }
          ]
        },
        srs: {
          state: 'review',
          difficulty: 0.3,
          stability: 5.0,
          due: new Date(Date.now() + 86400000 * 3).toISOString()
        }
      })
    }
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
