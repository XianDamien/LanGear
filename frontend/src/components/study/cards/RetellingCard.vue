<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import FlashcardContainer from '../modules/FlashcardContainer.vue'
import AudioRecorderPanel from '../modules/AudioRecorderPanel.vue'
import DualAudioPlayer from '../modules/DualAudioPlayer.vue'
import AIFeedbackPanel from '../modules/AIFeedbackPanel.vue'
import StudyNotesPanel from '../modules/StudyNotesPanel.vue'
import TranscriptComparisonPanel from '../TranscriptComparisonPanel.vue'
import GradeButtons from '../GradeButtons.vue'
import RetroButton from '@/components/ui/RetroButton.vue'
import type { Card, FsrsRating } from '@/types/domain'
import type { PollingResponseCompleted } from '@/types/api'

const props = defineProps<{
  card: Card
  isFlipped: boolean
  
  // Audio/Recording Props
  audioPlaying: boolean
  isRecording: boolean
  liveTranscript: string
  userTranscript: string
  userAudioUrl: string | null
  uploadState?: 'idle' | 'uploading' | 'uploaded' | 'failed'
  uploadProgress?: number
  
  // Feedback Props
  feedback: PollingResponseCompleted | null
  asyncSubmitState: string
  errorCode?: string | null
  errorMessage?: string | null
  
  // Translation Props
  showTranslation: boolean
  translationLoading: boolean
  
  // Notes
  notes: string
  
  // Rating
  ratingDisabled: boolean
}>()

const emit = defineEmits<{
  playReference: []
  toggleRecording: []
  flip: []
  showTranslation: []
  wordClick: [word: string]
  grade: [rating: FsrsRating]
  'update:notes': [value: string]
}>()

const audioPlayerRef = ref<InstanceType<typeof DualAudioPlayer> | null>(null)

function handleFlipClick() {
  if (props.isRecording) {
    ElMessage.warning('请先停止录音')
    return
  }
  emit('flip')
}

const recordingDisabled = computed(() => props.audioPlaying && !props.isRecording)

function handleTimestampClick(timestamp: number) {
  audioPlayerRef.value?.jumpToUserAudio(timestamp)
}
</script>

<template>
  <FlashcardContainer :is-flipped="isFlipped">
    <template #front>
      <AudioRecorderPanel
        :audio-playing="audioPlaying"
        :is-recording="isRecording"
        :live-transcript="liveTranscript"
        :user-transcript="userTranscript"
        :upload-state="uploadState"
        :upload-progress="uploadProgress"
        :recording-disabled="recordingDisabled"
        @play-reference="emit('playReference')"
        @toggle-recording="emit('toggleRecording')"
      />
      
      <p
        v-if="recordingDisabled"
        class="mt-4 text-center text-sm text-brand-alert"
      >
        建议完整听完原音频之后再录音
      </p>

      <RetroButton
        variant="primary"
        class="mt-8 w-full max-w-md"
        :disabled="uploadState === 'uploading'"
        data-testid="flip-button"
        @click="handleFlipClick"
      >
        翻面复盘
      </RetroButton>
    </template>

    <template #back>
      <div class="flex-1 min-h-0 space-y-5 overflow-y-auto pr-1 sm:pr-2">
        <DualAudioPlayer
          ref="audioPlayerRef"
          :reference-audio-url="card.frontAudio || null"
          :user-audio-url="userAudioUrl"
        />

        <TranscriptComparisonPanel
          :original-text="card.backText"
          :transcript-text="userTranscript"
          :translation-text="card.backTranslation || ''"
          :show-translation="showTranslation"
          :translation-loading="translationLoading"
          :nouns="card.grammarInfo?.nouns"
          :verbs="card.grammarInfo?.verbs"
          @word-click="emit('wordClick', $event)"
          @toggle-translation="emit('showTranslation')"
        />

        <AIFeedbackPanel
          :feedback="feedback"
          :loading="asyncSubmitState === 'processing' || asyncSubmitState === 'submitting'"
          :error-code="errorCode"
          :error-message="errorMessage"
          @timestamp-click="handleTimestampClick"
        />

        <StudyNotesPanel
          :notes="notes"
          @update:notes="emit('update:notes', $event)"
        />
      </div>

      <div class="mt-4 border-t border-slate-200/80 pt-4">
        <GradeButtons
          :disabled="ratingDisabled"
          @grade="emit('grade', $event)"
        />
      </div>
    </template>
  </FlashcardContainer>
</template>
