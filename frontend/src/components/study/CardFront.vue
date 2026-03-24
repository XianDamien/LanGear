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

const uploadStateText: Record<UploadState, string> = {
  idle: '等待上传',
  uploading: '上传中',
  uploaded: '上传完成',
  failed: '上传失败',
}

function handleFlipClick() {
  if (props.isRecording) {
    ElMessage.warning('请先停止录音')
    return
  }

  emit('flip')
}
</script>

<template>
  <div class="mx-auto flex h-full w-full max-w-3xl flex-col justify-between gap-4 sm:gap-5" data-testid="card-front">
    <div class="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
      <section class="rounded-[28px] border border-slate-200 bg-white p-5 shadow-mech sm:p-6">
        <div class="flex items-start justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <p class="font-pixel text-[0.72rem] tracking-[0.18em] text-brand-accent">REFERENCE</p>
            <h2 class="mt-2 text-lg font-semibold text-slate-900 sm:text-xl">先听原音，找准节奏</h2>
          </div>
          <span
            :class="[
              'rounded-full border px-3 py-1 text-[0.68rem] tracking-[0.16em]',
              audioPlaying
                ? 'border-brand-accent/20 bg-brand-accent/10 text-brand-accent'
                : 'border-slate-200 bg-slate-50 text-slate-500',
            ]"
          >
            {{ audioPlaying ? '播放中' : '待播放' }}
          </span>
        </div>

        <button
          type="button"
          :class="[
            'group relative mx-auto mt-6 flex h-32 w-32 items-center justify-center rounded-full border-[10px] transition-all duration-300 sm:h-36 sm:w-36',
            audioPlaying
              ? 'border-brand-accent bg-brand-accent/10 shadow-[0_0_0_10px_rgba(255,77,45,0.08)]'
              : 'border-slate-200 bg-slate-50 hover:border-brand-accent/40 hover:bg-brand-accent/5',
          ]"
          data-testid="play-reference-audio"
          @click="emit('playAudio')"
        >
          <span
            :class="[
              'absolute inset-3 rounded-full border transition-colors duration-300',
              audioPlaying ? 'border-brand-accent/30' : 'border-slate-200',
            ]"
          />
          <Volume2
            v-if="audioPlaying"
            :size="46"
            class="relative z-10 animate-pulse text-brand-accent"
          />
          <Play
            v-else
            :size="42"
            class="relative z-10 translate-x-0.5 text-slate-700 transition-transform group-hover:scale-105"
          />
        </button>

        <p class="mt-5 text-center text-sm leading-6 text-slate-500">
          点击播放标准音频，再开始复述。先建立语调和停顿，再进入录音。
        </p>
      </section>

      <section
        class="relative overflow-hidden rounded-[28px] border border-slate-900 bg-slate-950 p-5 text-white shadow-[0_24px_60px_rgba(15,23,42,0.18)] sm:p-6"
        data-testid="live-transcript"
      >
        <div class="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.05)_0%,transparent_32%,rgba(255,255,255,0.03)_100%)]" />
        <div class="pointer-events-none absolute inset-x-0 top-0 h-full bg-[linear-gradient(transparent_0%,rgba(255,255,255,0.04)_50%,transparent_100%)] bg-[length:100%_9px] opacity-40" />

        <div class="relative flex h-full min-h-[18rem] flex-col">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="font-pixel text-[0.72rem] tracking-[0.18em] text-brand-accent">LIVE ASR</p>
              <h2 class="mt-2 text-lg font-semibold sm:text-xl">实时复述监看区</h2>
            </div>
            <span
              :class="[
                'rounded-full border px-3 py-1 text-[0.68rem] tracking-[0.16em]',
                isRecording
                  ? 'border-rose-300/40 bg-rose-400/15 text-rose-100'
                  : 'border-white/10 bg-white/5 text-white/70',
              ]"
            >
              {{ isRecording ? '录音中' : '待录音' }}
            </span>
          </div>

          <div class="mt-5 flex-1 rounded-[24px] border border-white/10 bg-white/5 p-4 sm:p-5">
            <p class="text-[0.68rem] tracking-[0.22em] text-white/45">ASR 实时反馈</p>
            <div class="mt-4 min-h-[7.5rem] text-xl leading-relaxed text-white sm:text-2xl">
              {{ isRecording ? (liveTranscript || '...') : (userTranscript || '...') }}
            </div>
          </div>

          <div class="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs tracking-[0.14em] text-white/60">
            <span>状态: {{ isRecording ? '实时转写进行中' : '等待下一次录音' }}</span>
            <span>上传: {{ uploadStateText[uploadState ?? 'idle'] }}</span>
          </div>
        </div>
      </section>
    </div>

    <div class="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
      <section class="rounded-[28px] border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-5 shadow-mech sm:p-6">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="font-pixel text-[0.72rem] tracking-[0.18em] text-brand-accent">RECORD</p>
            <h2 class="mt-2 text-lg font-semibold text-slate-900 sm:text-xl">
              {{ isRecording ? '保持语速，完成本轮复述' : '准备开始录音复述' }}
            </h2>
          </div>
          <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-[0.68rem] tracking-[0.16em] text-slate-500">
            {{ isRecording ? 'REC' : 'READY' }}
          </span>
        </div>

        <RetroButton
          :variant="isRecording ? 'danger' : 'secondary'"
          class="mt-6 w-full min-h-[4.25rem] text-base sm:text-lg"
          data-testid="record-toggle"
          @click="emit('toggleRecording')"
        >
          <Square v-if="isRecording" class="animate-pulse" />
          <Mic v-else />
          {{ isRecording ? '停止录音' : '开始录音' }}
        </RetroButton>

        <p class="mt-4 text-sm leading-6 text-slate-500">
          {{ isRecording ? '结束后将保留本次实时转写结果。' : '建议先听一遍原音，再开始跟读复述。' }}
        </p>
      </section>

      <section class="flex flex-col justify-between rounded-[28px] border border-dashed border-slate-300 bg-slate-50/80 p-5 sm:p-6">
        <div>
          <p class="font-pixel text-[0.72rem] tracking-[0.18em] text-slate-500">REVIEW</p>
          <h2 class="mt-2 text-lg font-semibold text-slate-900 sm:text-xl">录完就翻面复盘</h2>
          <p class="mt-3 text-sm leading-6 text-slate-500">
            翻面后会自动上传录音并创建 AI 评测任务，完成后即可进行 FSRS 评分。
          </p>
        </div>

        <RetroButton
          variant="primary"
          class="mt-6 w-full min-h-[4.25rem] text-base sm:text-lg"
          :disabled="uploadState === 'uploading'"
          data-testid="flip-button"
          @click="handleFlipClick"
        >
          翻面复盘
        </RetroButton>
      </section>
    </div>

    <div
      v-if="uploadState === 'uploading'"
      class="rounded-[24px] border border-sky-200 bg-sky-50 p-4 shadow-mech-sm"
      data-testid="upload-progress"
    >
      <div class="mb-3 flex items-center gap-2">
        <Upload class="animate-pulse text-sky-600" :size="16" />
        <span class="text-sm font-semibold text-sky-900">录音上传中</span>
      </div>
      <div class="h-2.5 w-full rounded-full bg-sky-200">
        <div
          class="h-2.5 rounded-full bg-sky-600 transition-all"
          :style="{ width: `${uploadProgress || 0}%` }"
        />
      </div>
    </div>
  </div>
</template>
