import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { fetchLessonCards } from '@/services/api/decks'
import { submitReview, submitReviewAsync, pollSubmissionResult } from '@/services/api/study'
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
      cards.value = data.cards
      lessonName.value = data.lessonName
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
      URL.revokeObjectURL(userAudioUrl.value)
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

  /** @deprecated Use submitCardReviewAsync instead */
  async function submitCardReview(rating: Rating): Promise<'next' | 'summary'> {
    if (!lessonId.value || !currentCard.value) throw new Error('No active lesson')
    submitState.value = 'submitting'
    try {
      const { data } = await submitReview({
        lessonId: Number(lessonId.value.replace(/\D/g, '')) || 1,
        cardId: Number(currentCard.value.id.replace(/\D/g, '')) || 1,
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

  async function submitCardReviewAsync(
    rating: Rating,
    ossAudioPath: string
  ): Promise<'next' | 'summary' | 'poll'> {
    if (!lessonId.value || !currentCard.value) {
      throw new Error('No active lesson')
    }

    asyncSubmitState.value = 'submitting'

    try {
      const { data } = await submitReviewAsync({
        lesson_id: Number(lessonId.value.replace(/\D/g, '')) || 1,
        card_id: Number(currentCard.value.id.replace(/\D/g, '')) || 1,
        rating,
        oss_audio_path: ossAudioPath
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

  function startPolling(id: number) {
    stopPolling()

    const pollInterval = Number(import.meta.env.VITE_POLLING_INTERVAL) || 1500
    const timeout = Number(import.meta.env.VITE_POLLING_TIMEOUT) || 30000
    const startTime = Date.now()

    pollingInterval.value = window.setInterval(async () => {
      // 超时检查
      if (Date.now() - startTime > timeout) {
        stopPolling()
        asyncSubmitState.value = 'failed'
        ElMessage.error('处理超时，请稍后查看')
        return
      }

      try {
        const { data } = await pollSubmissionResult(id)

        if (data.status === 'completed') {
          stopPolling()
          asyncSubmitState.value = 'completed'
          lastFeedbackV2.value = data
          transcriptionTimestamps.value = data.transcription.timestamps
          userTranscript.value = data.transcription.text
          ElMessage.success('AI 评测完成')
        } else if (data.status === 'failed') {
          stopPolling()
          asyncSubmitState.value = 'failed'
          ElMessage.error(`处理失败：${data.error_message}`)
        }
        // status === 'processing' 时继续轮询
      } catch (error) {
        console.error('Polling error:', error)
        // 网络错误不停止轮询，自动重试
      }
    }, pollInterval)
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

  function flip() {
    isFlipped.value = true
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
    submitCardReviewAsync,
    startPolling,
    stopPolling,
    jumpToTimestamp
  }
})
