import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { fetchLessonCards } from '@/services/api/decks'
import {
  submitReview,
  submitReviewAsync,
  submitRating,
  getOSSSignedUrl,
} from '@/services/api/study'
import type { Card, Rating } from '@/types/domain'
import type {
  SubmitReviewResponse,
  PollingResponseCompleted,
  WordTimestamp,
} from '@/types/api'
import { parseNumericIdOrThrow } from '@/utils/ids'

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
  const transcriptionTimestamps = ref<WordTimestamp[]>([])
  const currentAudioElement = ref<HTMLAudioElement | null>(null)
  const lastFeedbackV2 = ref<PollingResponseCompleted | null>(null)

  const currentCard = computed(() => cards.value[currentIndex.value])
  const isLastCard = computed(() => currentIndex.value >= cards.value.length - 1)
  const progress = computed(() =>
    cards.value.length > 0 ? ((currentIndex.value + 1) / cards.value.length) * 100 : 0,
  )

  function resetTimestampAudio() {
    if (!currentAudioElement.value) return
    currentAudioElement.value.pause()
    currentAudioElement.value.currentTime = 0
    currentAudioElement.value = null
  }

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
    audioPlaying.value = false

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
    resetTimestampAudio()
  }

  /** @deprecated Use createFeedbackSubmission + submitCardRating instead */
  async function submitCardReview(rating: Rating): Promise<'next' | 'summary'> {
    if (!lessonId.value || !currentCard.value) throw new Error('No active lesson')

    const parsedLessonId = parseNumericIdOrThrow(lessonId.value, '课程 ID')
    const parsedCardId = parseNumericIdOrThrow(currentCard.value.id, '卡片 ID')

    submitState.value = 'submitting'
    try {
      const { data } = await submitReview({
        lessonId: parsedLessonId,
        cardId: parsedCardId,
        rating,
        userAudio: userAudioBase64.value || '',
        audioFormat: 'wav',
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
    realtimeSessionId: string,
  ): Promise<number> {
    if (!lessonId.value || !currentCard.value) {
      throw new Error('No active lesson')
    }

    const parsedLessonId = parseNumericIdOrThrow(lessonId.value, '课程 ID')
    const parsedCardId = parseNumericIdOrThrow(currentCard.value.id, '卡片 ID')

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
      return data.submission_id
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

  function jumpToTimestamp(timestamp: number) {
    if (!userAudioUrl.value) return

    if (!currentAudioElement.value || currentAudioElement.value.src !== userAudioUrl.value) {
      resetTimestampAudio()
      currentAudioElement.value = new Audio(userAudioUrl.value)
    }

    currentAudioElement.value.currentTime = timestamp
    void currentAudioElement.value.play().catch((error) => {
      console.warn('Failed to play timestamp audio:', error)
    })
  }

  function selectCard(index: number) {
    if (index < 0 || index >= cards.value.length) return
    currentIndex.value = index
    resetCardState()
  }

  function goNextCard() {
    if (!isLastCard.value) {
      selectCard(currentIndex.value + 1)
    }
  }

  async function flip() {
    isFlipped.value = true

    if (!userAudioUrl.value && currentCard.value?.ossAudioPath) {
      try {
        userAudioUrl.value = await getOSSSignedUrl(currentCard.value.ossAudioPath)
      } catch (error) {
        console.warn('Failed to get signed URL for recording:', error)
      }
    }
  }

  watch(userAudioUrl, (nextUrl, previousUrl) => {
    if (nextUrl !== previousUrl) {
      resetTimestampAudio()
    }
  })

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
    selectCard,
    goNextCard,
    flip,
    uploadState,
    asyncSubmitState,
    submissionId,
    transcriptionTimestamps,
    lastFeedbackV2,
    createFeedbackSubmission,
    submitCardRating,
    jumpToTimestamp,
    resetTimestampAudio,
  }
})
