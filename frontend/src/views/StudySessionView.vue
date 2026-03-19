<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useStudyStore } from '@/stores/study'
import { useRecorder } from '@/composables/useRecorder'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import { useRealtimeAsr } from '@/composables/useRealtimeAsr'
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
const realtimeAsr = useRealtimeAsr()

const isSummaryOpen = ref(false)
const summaryText = ref<string | null>(null)
const isSummaryLoading = ref(false)
const isFeedbackLoading = ref(false)
const isTranslationLoading = ref(false)

function parseNumericId(rawValue: string | null | undefined): number {
  return Number(String(rawValue ?? '').replace(/\D/g, '')) || 1
}

async function waitForRecordingBlob(timeoutMs = 2500): Promise<boolean> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    if (recorder.recordingBlob.value && recorder.audioUrl.value) return true
    await new Promise((resolve) => setTimeout(resolve, 50))
  }
  return false
}

async function waitForRealtimeSessionId(timeoutMs = 1200): Promise<boolean> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    if (realtimeAsr.realtimeSessionId.value) return true
    await new Promise((resolve) => setTimeout(resolve, 30))
  }
  return Boolean(realtimeAsr.realtimeSessionId.value)
}

onMounted(async () => {
  const lessonId = route.params.lessonId as string
  await studyStore.loadLessonCards(lessonId)
})

onUnmounted(() => {
  realtimeAsr.endSession()
  realtimeAsr.reset()
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

watch(currentIndex, () => {
  realtimeAsr.endSession()
  realtimeAsr.reset()
  recorder.reset()
})

function beginRecording() {
  realtimeAsr.finalTranscript.value = ''
  studyStore.recordingState = 'recording'
  studyStore.userTranscript = ''
  studyStore.liveTranscript = ''
  studyStore.uploadState = 'idle'
  studyStore.asyncSubmitState = 'idle'
}

function syncStoppedRecordingState() {
  studyStore.userAudioUrl = recorder.audioUrl.value
  studyStore.recordingState = 'stopped'
}

async function uploadRecordingForCurrentCard() {
  if (!currentCard.value) return

  studyStore.uploadState = 'uploading'
  const ossPath = await recorder.uploadToOSS(currentCard.value.id)

  if (ossPath) {
    studyStore.uploadState = 'uploaded'
    ElMessage.success('录音上传成功')
    return
  }

  studyStore.uploadState = 'failed'
}

async function handleStopRecordingFlow() {
  syncStoppedRecordingState()
  const committed = await realtimeAsr.commit()
  if (!committed || !realtimeAsr.finalTranscript.value.trim()) {
    ElMessage.warning('未获得实时转写结果，暂无法翻面')
    return
  }

  studyStore.liveTranscript = realtimeAsr.finalTranscript.value
  studyStore.userTranscript = realtimeAsr.finalTranscript.value
  studyStore.uploadState = 'idle'
}

async function startRealtimeForCurrentCard(): Promise<boolean> {
  if (!currentCard.value) return false
  const lessonId = parseNumericId(route.params.lessonId as string)
  const cardId = parseNumericId(currentCard.value.id)
  const connected = await realtimeAsr.connect(lessonId, cardId)
  const hasSessionId = connected ? await waitForRealtimeSessionId() : false
  if (!connected || !hasSessionId) {
    ElMessage.error('实时识别连接失败，请重试录音')
    return false
  }
  return true
}

function handleRealtimePcmChunk(chunkBase64: string) {
  if (!chunkBase64) return
  if (realtimeAsr.status.value === 'failed') return
  realtimeAsr.appendAudioChunk(chunkBase64)
}

async function toggleRecording() {
  if (recorder.isRecording.value) {
    recorder.stopRecording()
    const hasBlob = await waitForRecordingBlob()
    if (!hasBlob) {
      ElMessage.error('录音处理失败，请重试')
      return
    }
    await handleStopRecordingFlow()
  } else {
    realtimeAsr.endSession()
    realtimeAsr.reset()
    const connected = await startRealtimeForCurrentCard()
    if (!connected) return

    await recorder.startRecording(handleRealtimePcmChunk)
    beginRecording()
  }
}

async function handleGrade(rating: Rating) {
  if (!studyStore.submissionId) {
    ElMessage.warning('请先翻面等待 AI 反馈任务创建')
    return
  }

  if (asyncSubmitState.value !== 'completed') {
    ElMessage.info('AI 评测中，请稍候完成后再评分')
    return
  }

  try {
    const result = await studyStore.submitCardRating(rating)
    if (result === 'summary') {
      isSummaryOpen.value = true
    } else {
      studyStore.goNextCard()
    }
  } catch {
    ElMessage.error('评分提交失败，请重试')
  }
}

async function handleFlip() {
  if (recorder.isRecording.value) {
    ElMessage.warning('请先停止录音')
    return
  }

  if (!recorder.recordingBlob.value) {
    ElMessage.warning('请先完成录音后再翻面')
    return
  }

  if (!realtimeAsr.realtimeSessionId.value || !realtimeAsr.finalTranscript.value.trim()) {
    ElMessage.warning('未获得实时转写结果，暂无法翻面')
    return
  }

  if (realtimeAsr.status.value === 'failed') {
    ElMessage.error('实时识别连接失败，请重试录音')
    return
  }

  const realtimeSessionId = realtimeAsr.realtimeSessionId.value
  studyStore.userTranscript = realtimeAsr.finalTranscript.value
  studyStore.liveTranscript = realtimeAsr.finalTranscript.value

  await studyStore.flip()
  realtimeAsr.endSession()

  void (async () => {
    if (!currentCard.value) return

    if (studyStore.uploadState === 'uploading') return

    try {
      await uploadRecordingForCurrentCard()

      if (!recorder.ossAudioPath.value || studyStore.uploadState !== 'uploaded') {
        studyStore.asyncSubmitState = 'failed'
        return
      }

      studyStore.asyncSubmitState = 'submitting'
      await studyStore.createFeedbackSubmission(
        recorder.ossAudioPath.value,
        realtimeSessionId,
      )
      ElMessage.info('AI 评测中，请稍候...')
    } catch {
      studyStore.uploadState = 'failed'
      studyStore.asyncSubmitState = 'failed'
      ElMessage.error('提交失败，请重试')
    }
  })()
}

watch(asyncSubmitState, (newState) => {
  if (newState === 'completed' && studyStore.isLastCard) {
    setTimeout(() => {
      isSummaryOpen.value = true
    }, 1000)
  }
})

watch(
  () => realtimeAsr.partialTranscript.value,
  (text) => {
    if (!text) return
    studyStore.liveTranscript = text
  },
)

watch(
  () => realtimeAsr.finalTranscript.value,
  (text) => {
    if (!text) return
    studyStore.liveTranscript = text
    studyStore.userTranscript = text
  },
)

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
          @flip="handleFlip"
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
