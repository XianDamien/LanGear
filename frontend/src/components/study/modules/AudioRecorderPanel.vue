<script setup lang="ts">
import { Mic, Square, Upload, Volume2, Play } from 'lucide-vue-next'
import RetroButton from '@/components/ui/RetroButton.vue'

defineProps<{
  audioPlaying: boolean
  isRecording: boolean
  liveTranscript: string
  userTranscript: string
  uploadState?: 'idle' | 'uploading' | 'uploaded' | 'failed'
  uploadProgress?: number
  recordingDisabled?: boolean
}>()

const emit = defineEmits<{
  playReference: []
  toggleRecording: []
}>()
</script>

<template>
  <div class="mx-auto w-full max-w-md space-y-6">
    <!-- Play Reference button -->
    <div class="mb-8 flex justify-center">
      <div
        :class="[
          'p-4 rounded-full border-4 inline-flex items-center justify-center w-24 h-24 cursor-pointer hover:bg-slate-50 transition-colors',
          audioPlaying ? 'border-brand-accent animate-pulse' : 'border-slate-300',
        ]"
        data-testid="play-reference-audio"
        @click="emit('playReference')"
      >
        <Volume2
          v-if="audioPlaying"
          :size="40"
          class="text-brand-accent"
        />
        <Play
          v-else
          :size="40"
        />
      </div>
    </div>
    
    <p class="text-slate-500 text-sm uppercase tracking-widest text-center">
      听读跟读
    </p>

    <!-- Transcription area -->
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
        :disabled="recordingDisabled"
        data-testid="record-toggle"
        @click="emit('toggleRecording')"
      >
        <Square
          v-if="isRecording"
          class="mr-2 animate-pulse"
        />
        <Mic
          v-else
          class="mr-2"
        />
        {{ isRecording ? '停止' : '录音' }}
      </RetroButton>
    </div>

    <!-- Upload progress -->
    <div
      v-if="uploadState === 'uploading'"
      class="bg-blue-50 border border-blue-200 rounded p-3"
      data-testid="upload-progress"
    >
      <div class="mb-2 flex items-center gap-2">
        <Upload
          class="animate-pulse text-blue-600"
          :size="16"
        />
        <span class="text-sm text-blue-900">上传中... {{ uploadProgress }}%</span>
      </div>
      <div class="w-full bg-blue-200 rounded-full h-2">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all"
          :style="{ width: `${uploadProgress || 0}%` }"
        />
      </div>
    </div>
  </div>
</template>
