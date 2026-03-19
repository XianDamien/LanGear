<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useStudyStore } from '@/stores/study'
import { useStudyTasksStore } from '@/stores/studyTasks'
import { useRecorder } from '@/composables/useRecorder'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import { useRealtimeAsr } from '@/composables/useRealtimeAsr'
import RetroButton from '@/components/ui/RetroButton.vue'
import RetroCard from '@/components/ui/RetroCard.vue'
import CardFront from '@/components/study/CardFront.vue'
import CardBack from '@/components/study/CardBack.vue'
import StudyTaskNav from '@/components/study/StudyTaskNav.vue'
import WordExplanation from '@/components/study/WordExplanation.vue'
import SummaryModal from '@/components/summary/SummaryModal.vue'
import type { AsyncSubmitState } from '@/stores/study'
import type { Rating } from '@/types/domain'
import { parseNumericIdOrThrow } from '@/utils/ids'

const route = useRoute()
const router = useRouter()
const studyStore = useStudyStore()
const studyTasksStore = useStudyTasksStore()
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
} = storeToRefs(studyStore)
const { taskMap } = storeToRefs(studyTasksStore)

const recorder = useRecorder()
const audioPlayer = useAudioPlayer()
const realtimeAsr = useRealtimeAsr()

const isSummaryOpen = ref(false)
const summaryText = ref<string | null>(null)
const isSummaryLoading = ref(false)
const isFeedbackLoading = ref(false)
const isTranslationLoading = ref(false)

const studyCardClass = computed(() =>
  isFlipped.value
    ? 'flex h-full min-h-0 flex-col overflow-hidden p-4 sm:p-6 lg:p-8'
    : 'flex h-full min-h-0 flex-col items-center justify-center p-6 text-center sm:p-8',
)

const currentTask = computed(() =>
  currentCard.value ? studyTasksStore.getTask(currentCard.value.id) : null,
)
const currentSubmissionId = computed(() => currentTask.value?.submissionId ?? null)
const currentAsyncSubmitState = computed<AsyncSubmitState>(() => currentTask.value?.reviewState ?? 'idle')
const currentFeedbackV2 = computed(() => currentTask.value?.feedback ?? null)
const currentTranscriptionTimestamps = computed(
  () => currentTask.value?.feedback?.transcription.timestamps ?? [],
)
const displayedUserTranscript = computed(
  () => currentTask.value?.transcript || userTranscript.value,
)
const displayedUserAudioUrl = computed(
  () => userAudioUrl.value || currentTask.value?.audioUrl || null,
)

function shouldShowBackForCard(cardId: string | null | undefined): boolean {
  const task = studyTasksStore.getTask(cardId)
  return Boolean(task && (task.uploadState !== 'idle' || task.reviewState !== 'idle'))
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

function playCurrentAudio() {
  if (!currentCard.value) return
  if (currentCard.value.frontAudio) {
    audioPlayer.play(currentCard.value.frontAudio)
  } else {
    audioPlayer.speakText(currentCard.value.backText)
  }
}

function clearCardSession() {
  audioPlayer.stop()
  studyStore.audioPlaying = false
  studyStore.resetTimestampAudio()
  realtimeAsr.endSession()
  realtimeAsr.reset()
  recorder.reset()
}

async function loadStudySession(lessonId: string) {
  clearCardSession()
  studyTasksStore.resetSession()
  await studyStore.loadLessonCards(lessonId)
}

onUnmounted(() => {
  clearCardSession()
  studyTasksStore.resetSession()
  audioPlayer.stop()
})

watch(
  () => route.params.lessonId,
  async (lessonId) => {
    if (typeof lessonId !== 'string' || !lessonId) return
    await loadStudySession(lessonId)
  },
  { immediate: true },
)

watch(currentIndex, () => {
  clearCardSession()
})

watch(
  () => currentCard.value?.id,
  (cardId) => {
    const task = studyTasksStore.getTask(cardId)
    studyStore.setFlipped(shouldShowBackForCard(cardId))
    if (task?.audioUrl) {
      studyStore.userAudioUrl = task.audioUrl
    }
    if (task?.transcript) {
      studyStore.userTranscript = task.transcript
      studyStore.liveTranscript = task.transcript
    }
  },
  { immediate: true },
)

watch(
  () => audioPlayer.isPlaying.value,
  (isPlaying) => {
    studyStore.audioPlaying = isPlaying
  },
  { immediate: true },
)

function beginRecording() {
  realtimeAsr.finalTranscript.value = ''
  studyStore.recordingState = 'recording'
  studyStore.userTranscript = ''
  studyStore.liveTranscript = ''
  studyStore.uploadState = 'idle'
}

function syncStoppedRecordingState() {
  studyStore.userAudioUrl = recorder.audioUrl.value
  studyStore.recordingState = 'stopped'
}

async function uploadRecordingForCard(cardId: string): Promise<string | null> {
  studyStore.uploadState = 'uploading'
  const ossPath = await recorder.uploadToOSS(cardId)

  if (ossPath) {
    studyStore.uploadState = 'uploaded'
    ElMessage.success('录音上传成功')
    return ossPath
  }

  studyStore.uploadState = 'failed'
  return null
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

  try {
    const lessonId = parseNumericIdOrThrow(route.params.lessonId as string, '课程 ID')
    const cardId = parseNumericIdOrThrow(currentCard.value.id, '卡片 ID')
    const connected = await realtimeAsr.connect(lessonId, cardId)
    const hasSessionId = connected ? await waitForRealtimeSessionId() : false
    if (!connected || !hasSessionId) {
      ElMessage.error('实时识别连接失败，请重试录音')
      return false
    }
    return true
  } catch (error) {
    const message = error instanceof Error ? error.message : '无法开始录音'
    ElMessage.error(message)
    return false
  }
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

    const started = await recorder.startRecording(handleRealtimePcmChunk)
    if (!started) {
      realtimeAsr.endSession()
      realtimeAsr.reset()
      studyStore.recordingState = 'idle'
      return
    }

    beginRecording()
  }
}

async function handleGrade(rating: Rating) {
  if (!currentSubmissionId.value) {
    ElMessage.warning('请先翻面等待 AI 反馈任务创建')
    return
  }

  if (currentAsyncSubmitState.value !== 'completed') {
    ElMessage.info('AI 评测中，请稍候完成后再评分')
    return
  }

  try {
    const result = await studyStore.submitCardRating(currentSubmissionId.value, rating)
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
  if (!currentCard.value) return

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

  const cardId = currentCard.value.id
  const cardIndex = currentIndex.value
  const realtimeSessionId = realtimeAsr.realtimeSessionId.value
  const transcript = realtimeAsr.finalTranscript.value

  studyStore.userTranscript = transcript
  studyStore.liveTranscript = transcript
  await studyStore.flip()
  studyTasksStore.beginUpload(cardId, cardIndex, transcript)
  realtimeAsr.endSession()

  void (async () => {
    try {
      const ossPath = await uploadRecordingForCard(cardId)

      if (!ossPath) {
        studyTasksStore.markTaskFailed(cardId, cardIndex, '音频上传失败')
        return
      }

      studyTasksStore.markUploadUploaded(cardId, cardIndex)
      const submissionId = await studyStore.createFeedbackSubmission(
        cardId,
        ossPath,
        realtimeSessionId,
      )
      studyTasksStore.attachSubmission(cardId, cardIndex, submissionId, transcript)
      ElMessage.info('AI 评测中，请稍候...')
    } catch (error) {
      const message = error instanceof Error ? error.message : '提交失败，请重试'
      studyTasksStore.markTaskFailed(cardId, cardIndex, message)
      ElMessage.error(message)
    }
  })()
}

function handleSelectCard(index: number) {
  studyStore.setCurrentCard(index)
}

watch(currentAsyncSubmitState, (newState) => {
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
  <div class="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-4 py-4 sm:px-6 sm:py-6">
    <div class="mb-4 grid grid-cols-[minmax(5rem,1fr)_auto_minmax(5rem,1fr)] items-center gap-3 sm:mb-6">
      <div class="flex min-w-[5rem]">
        <RetroButton variant="ghost" size="sm" class="w-[5rem] justify-center" @click="exitStudy">
          退出
        </RetroButton>
      </div>
      <div class="min-w-0 text-center text-lg font-bold uppercase text-brand-accent sm:text-xl">
        {{ lessonName }}
        <span class="font-pixel">{{ currentIndex + 1 }}</span>
        /
        <span class="font-pixel">{{ cards.length }}</span>
      </div>
      <div class="min-w-[5rem]" aria-hidden="true" />
    </div>

    <StudyTaskNav
      v-if="cards.length"
      :cards="cards"
      :current-card-id="currentCard?.id"
      :tasks="taskMap"
      @select="handleSelectCard"
    />

    <div v-if="loading" class="flex-1 flex items-center justify-center text-slate-500">
      加载中...
    </div>

    <div v-else-if="currentCard" class="relative flex flex-1 min-h-0 flex-col pb-4">
      <RetroCard :class="studyCardClass">
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

        <CardBack
          v-else
          :card="currentCard"
          :user-transcript="displayedUserTranscript"
          :user-audio-url="displayedUserAudioUrl"
          :feedback="lastFeedback"
          :feedback-loading="isFeedbackLoading"
          :show-translation="showTranslation"
          :translation-loading="isTranslationLoading"
          :notes="notes"
          :submit-state="submitState"
          :async-submit-state="currentAsyncSubmitState"
          :feedback-v2="currentFeedbackV2"
          :transcription-timestamps="currentTranscriptionTimestamps"
          @play-original="playCurrentAudio"
          @show-translation="handleShowTranslation"
          @word-click="handleWordClick"
          @grade="handleGrade"
          @timestamp-jump="studyStore.jumpToTimestamp($event)"
          @update:notes="studyStore.notes = $event"
        />
      </RetroCard>

      <WordExplanation
        v-if="selectedWord"
        :word="selectedWord"
        :explanation="wordExplanation"
        @close="studyStore.selectedWord = null"
      />

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
