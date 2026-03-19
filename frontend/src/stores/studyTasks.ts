import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getOSSSignedUrl, pollSubmissionResult } from '@/services/api/study'
import type {
  PollingResponseCompleted,
  ProgressState,
} from '@/types/api'
import type { Card } from '@/types/domain'
import type { UploadState } from './study'

export type TaskReviewStatus = 'idle' | 'submitting' | 'processing' | 'completed' | 'failed'

export interface StudyTaskEntry {
  cardId: string
  cardIndex: number
  submissionId: number | null
  uploadState: UploadState
  reviewStatus: TaskReviewStatus
  progress: ProgressState | null
  result: PollingResponseCompleted | null
  signedAudioUrl: string | null
  errorCode: string | null
  errorMessage: string | null
  updatedAt: number | null
}

function createEmptyTask(cardId: string, cardIndex: number): StudyTaskEntry {
  return {
    cardId,
    cardIndex,
    submissionId: null,
    uploadState: 'idle',
    reviewStatus: 'idle',
    progress: null,
    result: null,
    signedAudioUrl: null,
    errorCode: null,
    errorMessage: null,
    updatedAt: null,
  }
}

export const useStudyTasksStore = defineStore('studyTasks', () => {
  const lessonId = ref<string | null>(null)
  const taskMap = ref<Record<string, StudyTaskEntry>>({})
  const pollingTimers = new Map<string, number>()

  const orderedTasks = computed(() =>
    Object.values(taskMap.value).sort((left, right) => left.cardIndex - right.cardIndex),
  )

  function ensureTask(cardId: string, cardIndex: number): StudyTaskEntry {
    const existing = taskMap.value[cardId]
    if (existing) {
      existing.cardIndex = cardIndex
      return existing
    }

    const nextTask = createEmptyTask(cardId, cardIndex)
    taskMap.value = {
      ...taskMap.value,
      [cardId]: nextTask,
    }
    return nextTask
  }

  function patchTask(cardId: string, cardIndex: number, patch: Partial<StudyTaskEntry>) {
    const current = ensureTask(cardId, cardIndex)
    taskMap.value = {
      ...taskMap.value,
      [cardId]: {
        ...current,
        ...patch,
        updatedAt: Date.now(),
      },
    }
  }

  function initializeLesson(nextLessonId: string, cards: Card[]) {
    if (lessonId.value !== nextLessonId) {
      teardown()
      lessonId.value = nextLessonId
    }

    const nextTaskMap: Record<string, StudyTaskEntry> = {}
    cards.forEach((card, index) => {
      nextTaskMap[card.id] = taskMap.value[card.id] ?? createEmptyTask(card.id, index)
      nextTaskMap[card.id]!.cardIndex = index
    })
    taskMap.value = nextTaskMap
  }

  function setUploadState(cardId: string, cardIndex: number, uploadState: UploadState) {
    patchTask(cardId, cardIndex, {
      uploadState,
      ...(uploadState === 'failed'
        ? { reviewStatus: 'failed', errorMessage: '上传失败' }
        : {}),
    })
  }

  function setSubmissionPending(cardId: string, cardIndex: number) {
    patchTask(cardId, cardIndex, {
      uploadState: 'uploaded',
      reviewStatus: 'submitting',
      errorCode: null,
      errorMessage: null,
    })
  }

  function setSubmissionFailed(cardId: string, cardIndex: number, errorMessage: string) {
    patchTask(cardId, cardIndex, {
      reviewStatus: 'failed',
      errorMessage,
    })
  }

  function stopPolling(cardId: string) {
    const timer = pollingTimers.get(cardId)
    if (!timer) return
    window.clearInterval(timer)
    pollingTimers.delete(cardId)
  }

  async function handleCompleted(cardId: string, cardIndex: number, data: PollingResponseCompleted) {
    stopPolling(cardId)

    const current = ensureTask(cardId, cardIndex)
    let signedAudioUrl = current.signedAudioUrl
    if (data.oss_audio_path && !signedAudioUrl) {
      try {
        signedAudioUrl = await getOSSSignedUrl(data.oss_audio_path)
      } catch (error) {
        console.warn('Failed to get task signed audio URL:', error)
      }
    }

    patchTask(cardId, cardIndex, {
      reviewStatus: 'completed',
      progress: null,
      result: data,
      signedAudioUrl: signedAudioUrl ?? null,
      errorCode: null,
      errorMessage: null,
    })
  }

  function handleFailed(cardId: string, cardIndex: number, errorCode: string | null, errorMessage: string) {
    stopPolling(cardId)
    patchTask(cardId, cardIndex, {
      reviewStatus: 'failed',
      progress: null,
      errorCode,
      errorMessage,
    })
  }

  function startPolling(cardId: string, cardIndex: number, submissionId: number) {
    stopPolling(cardId)

    const pollInterval = Number(import.meta.env.VITE_POLLING_INTERVAL) || 1500
    const timeout = Number(import.meta.env.VITE_POLLING_TIMEOUT) || 30000
    const startTime = Date.now()

    const timer = window.setInterval(async () => {
      if (Date.now() - startTime > timeout) {
        handleFailed(cardId, cardIndex, 'POLLING_TIMEOUT', '处理超时，请稍后查看')
        return
      }

      try {
        const { data } = await pollSubmissionResult(submissionId)
        if (data.status === 'completed') {
          await handleCompleted(cardId, cardIndex, data)
          return
        }

        if (data.status === 'failed') {
          handleFailed(cardId, cardIndex, data.error_code, data.error_message)
          return
        }

        patchTask(cardId, cardIndex, {
          reviewStatus: 'processing',
          progress: data.progress ?? null,
        })
      } catch (error) {
        console.error('Task polling error:', error)
      }
    }, pollInterval)

    pollingTimers.set(cardId, timer)
  }

  function registerSubmission(cardId: string, cardIndex: number, submissionId: number) {
    patchTask(cardId, cardIndex, {
      submissionId,
      uploadState: 'uploaded',
      reviewStatus: 'processing',
      progress: null,
      errorCode: null,
      errorMessage: null,
    })
    startPolling(cardId, cardIndex, submissionId)
  }

  function getTask(cardId: string | null | undefined): StudyTaskEntry | null {
    if (!cardId) return null
    return taskMap.value[cardId] ?? null
  }

  function teardown() {
    pollingTimers.forEach((timer) => window.clearInterval(timer))
    pollingTimers.clear()
    taskMap.value = {}
    lessonId.value = null
  }

  return {
    lessonId,
    taskMap,
    orderedTasks,
    initializeLesson,
    setUploadState,
    setSubmissionPending,
    setSubmissionFailed,
    registerSubmission,
    getTask,
    stopPolling,
    teardown,
  }
})
