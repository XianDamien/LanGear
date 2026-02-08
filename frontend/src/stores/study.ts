import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { fetchLessonCards } from '@/services/api/decks'
import { submitReview } from '@/services/api/study'
import type { Card, Rating } from '@/types/domain'
import type { SubmitReviewResponse } from '@/types/api'

export type RecordingState = 'idle' | 'recording' | 'stopped'
export type SubmitState = 'idle' | 'submitting' | 'success' | 'failed'

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
  }

  async function submitCardReview(rating: Rating): Promise<'next' | 'summary'> {
    if (!lessonId.value || !currentCard.value) throw new Error('No active lesson')
    submitState.value = 'submitting'
    try {
      const { data } = await submitReview({
        lessonId: Number(lessonId.value.replace(/\D/g, '')) || 1,
        cardId: Number(currentCard.value.id.replace(/\D/g, '')) || 1,
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
  }
})
