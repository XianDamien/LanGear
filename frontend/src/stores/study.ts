import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { fetchLessonCards } from '@/services/api/decks'
import {
  submitReview,
  submitReviewAsync,
  submitRating,
  pollSubmissionResult,
  getOSSSignedUrl,
} from '@/services/api/study'
import type { Card, Rating } from '@/types/domain'
import type {
  SubmitReviewResponse,
  PollingResponseCompleted,
  WordTimestamp
} from '@/types/api'

export type RecordingState = 'idle' | 'recording' | 'stopped'
export type SubmitState = 'idle' | 'submitting' | 'success' | 'failed'
export type AsyncSubmitState = 'idle' | 'submitting' | 'processing' | 'completed' | 'failed'
export type UploadState = 'idle' | 'uploading' | 'uploaded' | 'failed'

interface BackendLessonCard {
  id: string | number
  front_text?: string
  frontText?: string
  back_text?: string
  backTranslation?: string
  audio_path?: string
  frontAudio?: string
  difficulty?: number
  oss_audio_path?: string | null
  grammarInfo?: Card['grammarInfo']
}

interface BackendLessonCardsData {
  cards?: BackendLessonCard[]
  lessonName?: string
  lesson_name?: string
}

function parseNumericId(rawValue: string | null | undefined): number {
  return Number(String(rawValue ?? '').replace(/\D/g, '')) || 1
}

function mapBackendCardToDomain(raw: BackendLessonCard): Card {
  return {
    id: String(raw.id),
    frontText: raw.front_text ?? raw.frontText ?? '',
    backText: raw.front_text ?? raw.frontText ?? '',
    backTranslation: raw.back_text ?? raw.backTranslation ?? '',
    frontAudio: raw.audio_path ?? raw.frontAudio ?? '',
    difficulty: raw.difficulty ?? 0,
    ossAudioPath: raw.oss_audio_path ?? null,
    grammarInfo: raw.grammarInfo ?? undefined,
  }
}

export const useStudyStore = defineStore('study', () => {
  const lessonId = ref<string | null>(null)
  const lessonName = ref('')
  const cards = ref<Card[]>([])
  const currentIndex = ref(0)
  const isFlipped = ref(false)
  const recordingState = ref<RecordingState>('idle')
  const submitState = ref<SubmitState>('idle')
  const lastFeedback = ref<SubmitReviewResponse | null>(null)
  const userTranscript = ref('')
  const liveTranscript = ref('')
  const userAudioUrl = ref<string | null>(null)
  const userAudioBase64 = ref<string | null>(null)
  const notes = ref('')
  const showTranslation = ref(false)
  const audioPlaying = ref(false)
  const selectedWord = ref<string | null>(null)
  const wordExplanation = ref('')
  const loading = ref(false)

  const uploadState = ref<UploadState>('idle')
  const asyncSubmitState = ref<AsyncSubmitState>('idle')
  const submissionId = ref<number | null>(null)
  const pollingInterval = ref<number | null>(null)
  const transcriptionTimestamps = ref<WordTimestamp[]>([])
  const currentAudioElement = ref<HTMLAudioElement | null>(null)
  const lastFeedbackV2 = ref<PollingResponseCompleted | null>(null)

  const currentCard = computed(() => cards.value[currentIndex.value])
  const isLastCard = computed(() => currentIndex.value >= cards.value.length - 1)
  const progress = computed(() =>
    cards.value.length > 0 ? ((currentIndex.value + 1) / cards.value.length) * 100 : 0,
  )

  async function loadLessonCards(id: string) {
    loading.value = true
    lessonId.value = id
    try {
      const { data } = await fetchLessonCards(id)
      const payload = data as BackendLessonCardsData
      cards.value = (payload.cards ?? []).map(mapBackendCardToDomain)
      lessonName.value = payload.lessonName ?? payload.lesson_name ?? ''
      currentIndex.value = 0
      resetCardState()
    } finally {
      loading.value = false
    }
  }

  function resetCardState() {
    isFlipped.value = false
    recordingState.value = 'idle'
    submitState.value = 'idle'
    lastFeedback.value = null
    userTranscript.value = ''
    liveTranscript.value = ''
    notes.value = ''
    showTranslation.value = false
    selectedWord.value = null
    wordExplanation.value = ''
    if (userAudioUrl.value) {
      if (userAudioUrl.value.startsWith('blob:')) {
        URL.revokeObjectURL(userAudioUrl.value)
      }
      userAudioUrl.value = null
    }
    userAudioBase64.value = null

    uploadState.value = 'idle'
    asyncSubmitState.value = 'idle'
    submissionId.value = null
    transcriptionTimestamps.value = []
    lastFeedbackV2.value = null
    stopPolling()
  }

  /** @deprecated Use createFeedbackSubmission + submitCardRating instead */
  async function submitCardReview(rating: Rating): Promise<'next' | 'summary'> {
    if (!lessonId.value || !currentCard.value) throw new Error('No active lesson')
    const parsedLessonId = parseNumericId(lessonId.value)
    const parsedCardId = parseNumericId(currentCard.value.id)

    submitState.value = 'submitting'
    try {
      const { data } = await submitReview({
        lessonId: parsedLessonId,
        cardId: parsedCardId,
        rating,
        userAudio: userAudioBase64.value || '',
        audioFormat: 'wav'
      })
      lastFeedback.value = data
      submitState.value = 'success'

      if (isLastCard.value) {
        return 'summary'
      }
      return 'next'
    } catch {
      submitState.value = 'failed'
      throw new Error('提交失败，请重试')
    }
  }

  async function createFeedbackSubmission(
    ossAudioPath: string,
    realtimeSessionId: string
  ): Promise<'poll'> {
    if (!lessonId.value || !currentCard.value) {
      throw new Error('No active lesson')
    }

    const parsedLessonId = parseNumericId(lessonId.value)
    const parsedCardId = parseNumericId(currentCard.value.id)

    asyncSubmitState.value = 'submitting'

    try {
      const transcriptionText = userTranscript.value.trim() || liveTranscript.value.trim()
      const { data } = await submitReviewAsync({
        lesson_id: parsedLessonId,
        card_id: parsedCardId,
        oss_audio_path: ossAudioPath,
        realtime_session_id: realtimeSessionId,
        ...(transcriptionText ? { transcription_text: transcriptionText } : {}),
      })

      submissionId.value = data.submission_id
      asyncSubmitState.value = 'processing'

      // 启动轮询
      startPolling(data.submission_id)

      return 'poll'
    } catch {
      asyncSubmitState.value = 'failed'
      throw new Error('提交失败，请重试')
    }
  }

  async function submitCardRating(rating: Rating): Promise<'next' | 'summary'> {
    if (!submissionId.value) {
      throw new Error('No active submission')
    }

    submitState.value = 'submitting'
    try {
      await submitRating(submissionId.value, { rating })
      submitState.value = 'success'
      if (isLastCard.value) {
        return 'summary'
      }
      return 'next'
    } catch {
      submitState.value = 'failed'
      throw new Error('评分提交失败，请重试')
    }
  }

  function startPolling(id: number) {
    stopPolling()

    const pollInterval = Number(import.meta.env.VITE_POLLING_INTERVAL) || 1500
    const timeout = Number(import.meta.env.VITE_POLLING_TIMEOUT) || 30000
    const startTime = Date.now()

    pollingInterval.value = window.setInterval(async () => {
      // 超时检查
      if (Date.now() - startTime > timeout) {
        handlePollingTimeout()
        return
      }

      try {
        const { data } = await pollSubmissionResult(id)

        if (data.status === 'completed') {
          await handlePollingCompleted(data)
        } else if (data.status === 'failed') {
          handlePollingFailed(data.error_message)
        }
        // status === 'processing' 时继续轮询
      } catch (error) {
        console.error('Polling error:', error)
        // 网络错误不停止轮询，自动重试
      }
    }, pollInterval)
  }

  function handlePollingTimeout() {
    stopPolling()
    asyncSubmitState.value = 'failed'
    ElMessage.error('处理超时，请稍后查看')
  }

  async function handlePollingCompleted(data: PollingResponseCompleted) {
    stopPolling()
    asyncSubmitState.value = 'completed'
    lastFeedbackV2.value = data
    transcriptionTimestamps.value = data.transcription.timestamps
    userTranscript.value = data.transcription.text

    if (!userAudioUrl.value && data.oss_audio_path) {
      try {
        userAudioUrl.value = await getOSSSignedUrl(data.oss_audio_path)
      } catch (error) {
        console.warn('Failed to get signed URL:', error)
      }
    }

    ElMessage.success('AI 评测完成')
  }

  function handlePollingFailed(errorMessage: string) {
    stopPolling()
    asyncSubmitState.value = 'failed'
    ElMessage.error(`处理失败：${errorMessage}`)
  }

  function stopPolling() {
    if (pollingInterval.value) {
      window.clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
  }

  function jumpToTimestamp(timestamp: number) {
    if (userAudioUrl.value) {
      if (!currentAudioElement.value) {
        currentAudioElement.value = new Audio(userAudioUrl.value)
      }
      currentAudioElement.value.currentTime = timestamp
      currentAudioElement.value.play()
    }
  }

  function goNextCard() {
    if (!isLastCard.value) {
      currentIndex.value++
      resetCardState()
    }
  }

  async function flip() {
    isFlipped.value = true

    // Load signed URL for user recording if no local blob URL available
    if (!userAudioUrl.value && currentCard.value?.ossAudioPath) {
      try {
        userAudioUrl.value = await getOSSSignedUrl(currentCard.value.ossAudioPath)
      } catch (e) {
        console.warn('Failed to get signed URL for recording:', e)
      }
    }
  }

  return {
    lessonId,
    lessonName,
    cards,
    currentIndex,
    isFlipped,
    recordingState,
    submitState,
    lastFeedback,
    userTranscript,
    liveTranscript,
    userAudioUrl,
    userAudioBase64,
    notes,
    showTranslation,
    audioPlaying,
    selectedWord,
    wordExplanation,
    loading,
    currentCard,
    isLastCard,
    progress,
    loadLessonCards,
    resetCardState,
    submitCardReview,
    goNextCard,
    flip,
    uploadState,
    asyncSubmitState,
    submissionId,
    transcriptionTimestamps,
    lastFeedbackV2,
    createFeedbackSubmission,
    submitCardRating,
    startPolling,
    stopPolling,
    jumpToTimestamp
  }
})
