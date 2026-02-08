<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useStudyStore } from '@/stores/study'
import { useRecorder } from '@/composables/useRecorder'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import { ElMessage } from 'element-plus'
import RetroButton from '@/components/ui/RetroButton.vue'
import RetroCard from '@/components/ui/RetroCard.vue'
import CardFront from '@/components/study/CardFront.vue'
import CardBack from '@/components/study/CardBack.vue'
import WordExplanation from '@/components/study/WordExplanation.vue'
import SummaryModal from '@/components/summary/SummaryModal.vue'
import type { Rating } from '@/types/domain'

const route = useRoute()
const router = useRouter()
const studyStore = useStudyStore()
const {
  cards,
  currentIndex,
  currentCard,
  isFlipped,
  lastFeedback,
  submitState,
  userTranscript,
  liveTranscript,
  userAudioUrl,
  notes,
  showTranslation,
  selectedWord,
  wordExplanation,
  loading,
  lessonName,
  audioPlaying,
  uploadState,
  asyncSubmitState,
  transcriptionTimestamps,
  lastFeedbackV2
} = storeToRefs(studyStore)

const recorder = useRecorder()
const audioPlayer = useAudioPlayer()

const isSummaryOpen = ref(false)
const summaryText = ref<string | null>(null)
const isSummaryLoading = ref(false)
const isFeedbackLoading = ref(false)
const isTranslationLoading = ref(false)

// ASR simulation
let asrInterval: number | null = null

function stopAsrStream() {
  if (asrInterval) {
    window.clearInterval(asrInterval)
    asrInterval = null
  }
}

function startAsrStream() {
  stopAsrStream()
  studyStore.liveTranscript = ''
  if (!currentCard.value) return
  const words = currentCard.value.backText.split(' ')
  let idx = 0
  asrInterval = window.setInterval(() => {
    idx = Math.min(words.length, idx + 1)
    studyStore.liveTranscript = words.slice(0, idx).join(' ')
    if (idx >= words.length) stopAsrStream()
  }, 400)
}

onMounted(async () => {
  const lessonId = route.params.lessonId as string
  await studyStore.loadLessonCards(lessonId)
  playCurrentAudio()
})

onUnmounted(() => {
  stopAsrStream()
  recorder.reset()
  studyStore.stopPolling()
  audioPlayer.stop()
})

function playCurrentAudio() {
  if (!currentCard.value) return
  studyStore.audioPlaying = true
  if (currentCard.value.frontAudio) {
    audioPlayer.play(currentCard.value.frontAudio)
  } else {
    audioPlayer.speakText(currentCard.value.backText)
  }
  // Sync playing state
  const checkPlaying = setInterval(() => {
    if (!audioPlayer.isPlaying.value) {
      studyStore.audioPlaying = false
      clearInterval(checkPlaying)
    }
  }, 200)
}

// Reset state when card index changes
watch(currentIndex, () => {
  stopAsrStream()
  recorder.reset()
  playCurrentAudio()
})

async function toggleRecording() {
  if (recorder.isRecording.value) {
    recorder.stopRecording()
    stopAsrStream()

    setTimeout(async () => {
      if (!currentCard.value) return

      studyStore.userTranscript = studyStore.liveTranscript || '（未识别到内容）'
      studyStore.userAudioUrl = recorder.audioUrl.value
      studyStore.recordingState = 'stopped'

      studyStore.uploadState = 'uploading'
      const ossPath = await recorder.uploadToOSS(currentCard.value.id)
      if (ossPath) {
        studyStore.uploadState = 'uploaded'
        ElMessage.success('录音上传成功')
      } else {
        studyStore.uploadState = 'failed'
      }
    }, 300)
  } else {
    await recorder.startRecording()
    studyStore.recordingState = 'recording'
    studyStore.userTranscript = ''
    startAsrStream()
  }
}

async function handleGrade(rating: Rating) {
  if (!recorder.ossAudioPath.value) {
    ElMessage.error('请先完成录音并上传')
    return
  }

  try {
    await studyStore.submitCardReviewAsync(rating, recorder.ossAudioPath.value)
    ElMessage.info('AI 评测中，请稍候...')
  } catch {
    ElMessage.error('提交失败，请重试')
  }
}

watch(asyncSubmitState, (newState) => {
  if (newState === 'completed' && studyStore.isLastCard) {
    setTimeout(() => {
      isSummaryOpen.value = true
    }, 1000)
  }
})

function handleWordClick(word: string) {
  studyStore.selectedWord = word
  studyStore.wordExplanation = '正在加载 AI 解析...'
  // Mock explanation
  setTimeout(() => {
    studyStore.wordExplanation = `"${word}" 是本句中的关键词。在此语境下表示...（AI 解析示例）`
  }, 800)
}

function handleShowTranslation() {
  studyStore.showTranslation = true
  if (currentCard.value?.backTranslation) return
  isTranslationLoading.value = true
  setTimeout(() => {
    isTranslationLoading.value = false
  }, 1000)
}

function handleSummary() {
  isSummaryLoading.value = true
  summaryText.value = null
  setTimeout(() => {
    summaryText.value = '本课已完成。建议重点关注发音连读与动词时态变化，并回听不顺畅的句子。'
    isSummaryLoading.value = false
  }, 1200)
}

function exitSummary() {
  isSummaryOpen.value = false
  const lessonId = route.params.lessonId as string
  router.push(`/summary/${lessonId}`)
}

function exitStudy() {
  router.push('/library')
}
</script>

<template>
  <div class="max-w-4xl mx-auto p-4 flex flex-col h-[85vh]">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <RetroButton variant="ghost" size="sm" @click="exitStudy">
        退出
      </RetroButton>
      <div class="text-xl text-brand-accent font-bold uppercase">
        {{ lessonName }}
        <span class="font-pixel">{{ currentIndex + 1 }}</span>
        /
        <span class="font-pixel">{{ cards.length }}</span>
      </div>
      <div class="w-10" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-slate-500">
      加载中...
    </div>

    <!-- Card area -->
    <div v-else-if="currentCard" class="flex-1 relative">
      <RetroCard
        class="h-full flex flex-col justify-center items-center text-center p-8 transition-all duration-500"
      >
        <!-- Front -->
        <CardFront
          v-if="!isFlipped"
          :audio-playing="audioPlaying"
          :is-recording="recorder.isRecording.value"
          :live-transcript="liveTranscript"
          :user-transcript="userTranscript"
          :upload-state="uploadState"
          :upload-progress="recorder.uploadProgress.value"
          @play-audio="playCurrentAudio"
          @toggle-recording="toggleRecording"
          @flip="studyStore.flip()"
        />

        <!-- Back -->
        <CardBack
          v-else
          :card="currentCard"
          :user-transcript="userTranscript"
          :user-audio-url="userAudioUrl"
          :feedback="lastFeedback"
          :feedback-loading="isFeedbackLoading"
          :show-translation="showTranslation"
          :translation-loading="isTranslationLoading"
          :notes="notes"
          :submit-state="submitState"
          :async-submit-state="asyncSubmitState"
          :feedback-v2="lastFeedbackV2"
          :transcription-timestamps="transcriptionTimestamps"
          @play-original="playCurrentAudio"
          @show-translation="handleShowTranslation"
          @word-click="handleWordClick"
          @grade="handleGrade"
          @timestamp-jump="studyStore.jumpToTimestamp($event)"
          @update:notes="studyStore.notes = $event"
        />
      </RetroCard>

      <!-- Word explanation popup -->
      <WordExplanation
        v-if="selectedWord"
        :word="selectedWord"
        :explanation="wordExplanation"
        @close="studyStore.selectedWord = null"
      />

      <!-- Summary modal -->
      <SummaryModal
        v-if="isSummaryOpen"
        :loading="isSummaryLoading"
        :summary-text="summaryText"
        @generate="handleSummary"
        @exit="exitSummary"
      />
    </div>
  </div>
</template>
