<script setup lang="ts">
import { Mic, Play, Volume2, Square } from 'lucide-vue-next'
import RetroButton from '@/components/ui/RetroButton.vue'

defineProps<{
  audioPlaying: boolean
  isRecording: boolean
  liveTranscript: string
  userTranscript: string
}>()

const emit = defineEmits<{
  playAudio: []
  toggleRecording: []
  flip: []
}>()
</script>

<template>
  <div class="w-full max-w-md space-y-6 mx-auto">
    <!-- Play button -->
    <div class="flex justify-center mb-8">
      <div
        :class="[
          'p-4 rounded-full border-4 inline-flex items-center justify-center w-24 h-24 cursor-pointer hover:bg-slate-50',
          audioPlaying ? 'border-brand-accent animate-pulse' : 'border-slate-300',
        ]"
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
        @click="emit('toggleRecording')"
      >
        <Square v-if="isRecording" class="mr-2 animate-pulse" />
        <Mic v-else class="mr-2" />
        {{ isRecording ? '停止' : '录音' }}
      </RetroButton>
    </div>

    <!-- Flip button -->
    <RetroButton
      variant="primary"
      class="w-full mt-4"
      :disabled="isRecording"
      @click="emit('flip')"
    >
      翻面复盘
    </RetroButton>
  </div>
</template>
