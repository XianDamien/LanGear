<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Pause, Play, Volume2 } from 'lucide-vue-next'

const props = defineProps<{
  label: string
  src: string | null
  hint?: string
  channel?: string
}>()

const emit = defineEmits<{
  play: []
}>()

const audioElement = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

const hasSource = computed(() => Boolean(props.src))
const stateLabel = computed(() => {
  if (!hasSource.value) return 'Unavailable'
  if (isPlaying.value) return 'Playing'
  return duration.value > 0 ? 'Ready' : 'Loading'
})

function formatTime(seconds: number): string {
  const safeValue = Number.isFinite(seconds) ? Math.max(0, seconds) : 0
  const minutes = Math.floor(safeValue / 60)
  const remainder = Math.floor(safeValue % 60)
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
}

function syncFromAudio() {
  if (!audioElement.value) return
  currentTime.value = audioElement.value.currentTime || 0
  duration.value = Number.isFinite(audioElement.value.duration) ? audioElement.value.duration : 0
}

function handleLoadedMetadata() {
  syncFromAudio()
}

function handleTimeUpdate() {
  syncFromAudio()
}

function handleEnded() {
  isPlaying.value = false
  syncFromAudio()
}

async function requestPlay() {
  if (!audioElement.value || !hasSource.value) return
  emit('play')
  try {
    await audioElement.value.play()
    isPlaying.value = true
  } catch (error) {
    isPlaying.value = false
    console.warn('Failed to play audio:', error)
  }
}

function pause() {
  if (!audioElement.value) return
  audioElement.value.pause()
  isPlaying.value = false
}

function reset() {
  pause()
  currentTime.value = 0
  duration.value = 0
}

function togglePlayback() {
  if (!audioElement.value || !hasSource.value) return
  if (isPlaying.value) {
    pause()
    return
  }
  void requestPlay()
}

function handleSeek(event: Event) {
  if (!audioElement.value || !hasSource.value) return
  const nextValue = Number((event.target as HTMLInputElement).value)
  if (Number.isNaN(nextValue)) return
  audioElement.value.currentTime = nextValue
  currentTime.value = nextValue
}

function waitForMetadata(audio: HTMLAudioElement): Promise<void> {
  if (Number.isFinite(audio.duration) && audio.duration > 0) {
    return Promise.resolve()
  }

  return new Promise((resolve) => {
    const cleanup = () => {
      audio.removeEventListener('loadedmetadata', handleReady)
      audio.removeEventListener('canplay', handleReady)
    }
    const handleReady = () => {
      cleanup()
      resolve()
    }

    audio.addEventListener('loadedmetadata', handleReady, { once: true })
    audio.addEventListener('canplay', handleReady, { once: true })
    audio.load()
  })
}

async function jumpTo(timestamp: number) {
  if (!audioElement.value || !hasSource.value) return
  emit('play')
  await waitForMetadata(audioElement.value)
  const maxTime = duration.value > 0 ? duration.value : audioElement.value.duration || timestamp
  audioElement.value.currentTime = Math.min(Math.max(timestamp, 0), maxTime)
  currentTime.value = audioElement.value.currentTime
  await requestPlay()
}

watch(
  () => props.src,
  () => {
    reset()
  },
)

onBeforeUnmount(() => {
  reset()
})

defineExpose({
  pause,
  jumpTo,
})
</script>

<template>
  <section
    class="rounded-[1.75rem] border border-slate-200 bg-gradient-to-br from-white via-slate-50 to-slate-100/90 p-4 shadow-mech"
  >
    <audio
      ref="audioElement"
      :src="src || undefined"
      preload="metadata"
      @loadedmetadata="handleLoadedMetadata"
      @timeupdate="handleTimeUpdate"
      @ended="handleEnded"
      @pause="isPlaying = false"
      @play="isPlaying = true"
    />

    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <span
            v-if="channel"
            class="rounded-full border border-slate-300 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.24em] text-slate-500"
          >
            {{ channel }}
          </span>
          <span class="text-[10px] font-bold uppercase tracking-[0.32em] text-slate-400">
            {{ stateLabel }}
          </span>
        </div>
        <h3 class="mt-2 text-base font-semibold text-slate-900">{{ label }}</h3>
        <p class="mt-1 text-sm leading-6 text-slate-500">
          {{ hint || (hasSource ? '可独立播放和拖动进度。' : '当前卡片还没有可播放的音频。') }}
        </p>
      </div>

      <button
        type="button"
        class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-900 transition hover:border-brand-accent hover:text-brand-accent disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-300"
        :disabled="!hasSource"
        @click="togglePlayback"
      >
        <Pause v-if="isPlaying" :size="20" />
        <Play v-else-if="hasSource" :size="20" />
        <Volume2 v-else :size="20" />
      </button>
    </div>

    <div class="mt-5 rounded-2xl border border-slate-200 bg-white/90 p-3">
      <input
        class="h-2 w-full cursor-pointer accent-brand-accent disabled:cursor-not-allowed"
        type="range"
        :disabled="!hasSource"
        :max="duration || 0"
        :step="0.1"
        :value="currentTime"
        @input="handleSeek"
      >
      <div class="mt-3 flex items-center justify-between text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
        <span>{{ formatTime(currentTime) }}</span>
        <span>{{ hasSource ? formatTime(duration) : '--:--' }}</span>
      </div>
    </div>
  </section>
</template>
