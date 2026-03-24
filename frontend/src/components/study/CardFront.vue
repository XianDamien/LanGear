<script setup lang="ts">
import { Mic, Play, Volume2, Square, Upload } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import RetroButton from '@/components/ui/RetroButton.vue'
import type { UploadState } from '@/stores/study'

const props = defineProps<{
  audioPlaying: boolean
  isRecording: boolean
  liveTranscript: string
  userTranscript: string
  uploadState?: UploadState
  uploadProgress?: number
}>()

const emit = defineEmits<{
  playAudio: []
  toggleRecording: []
  flip: []
}>()

function handleFlipClick() {
  if (props.isRecording) {
    ElMessage.warning('请先停止录音')
    return
  }

  emit('flip')
}

function handleToggleRecordingClick() {
  if (props.audioPlaying && !props.isRecording) {
    ElMessage.warning('建议完整听完原音频之后再录音')
    return
  }

  emit('toggleRecording')
}
</script>

<template>
  <div class="w-full max-w-md space-y-6 mx-auto" data-testid="card-front">
    <!-- Play button -->
    <div class="flex justify-center mb-8">
      <div
        :class="[
          'p-4 rounded-full border-4 inline-flex items-center justify-center w-24 h-24 cursor-pointer hover:bg-slate-50',
          audioPlaying ? 'border-brand-accent animate-pulse' : 'border-slate-300',
        ]"
        data-testid="play-reference-audio"
        @click="emit('playAudio')"
      >
        <Volume2 v-if="audioPlaying" :size="40" class="text-brand-accent" />
        <Play v-else :size="40" />
      </div>
    </div>
    <p class="text-slate-500 text-sm uppercase tracking-widest text-center">
      听读跟读
    </p>

    <!-- Live transcript -->
    <div
      class="min-h-[60px] text-brand-accent font-sans text-lg border-b border-slate-200 pb-2"
      data-testid="live-transcript"
    >
      {{ isRecording ? (liveTranscript || '...') : (userTranscript || '...') }}
    </div>
    <div class="flex items-center justify-between text-xs uppercase text-slate-500">
      <span>ASR 实时反馈</span>
    </div>

    <!-- Record button -->
    <div class="flex justify-center gap-4">
      <RetroButton
        :variant="isRecording ? 'danger' : 'secondary'"
        class="w-full"
        data-testid="record-toggle"
        @click="handleToggleRecordingClick"
      >
        <Square v-if="isRecording" class="mr-2 animate-pulse" />
        <Mic v-else class="mr-2" />
        {{ isRecording ? '停止' : '录音' }}
      </RetroButton>
    </div>

    <!-- v2.0: 上传进度指示器 -->
    <div
      v-if="uploadState === 'uploading'"
      class="bg-blue-50 border border-blue-200 rounded p-3"
      data-testid="upload-progress"
    >
      <div class="flex items-center gap-2 mb-2">
        <Upload class="animate-pulse text-blue-600" :size="16" />
        <span class="text-sm text-blue-900">上传中...</span>
      </div>
      <div class="w-full bg-blue-200 rounded-full h-2">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all"
          :style="{ width: `${uploadProgress || 0}%` }"
        />
      </div>
    </div>

    <!-- Flip button -->
    <RetroButton
      variant="primary"
      class="w-full mt-4"
      :disabled="uploadState === 'uploading'"
      data-testid="flip-button"
      @click="handleFlipClick"
    >
      翻面复盘
    </RetroButton>
  </div>
</template>
