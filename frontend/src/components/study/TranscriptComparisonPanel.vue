<script setup lang="ts">
import { computed } from 'vue'
import { Languages } from 'lucide-vue-next'
import { buildTranscriptDiff, type DiffTokenView } from '@/utils/transcriptDiff'

const props = defineProps<{
  originalText: string
  transcriptText: string
  translationText: string
  showTranslation: boolean
  translationLoading: boolean
  nouns?: string[]
  verbs?: string[]
}>()

const emit = defineEmits<{
  wordClick: [word: string]
  toggleTranslation: []
}>()

const diffRows = computed(() => buildTranscriptDiff(props.originalText, props.transcriptText))

function tokenClasses(token: DiffTokenView, side: 'original' | 'transcript') {
  const classes = [
    'inline-flex min-h-[2rem] items-center rounded-xl border px-2.5 py-1 text-[15px] leading-6 transition-colors',
  ]

  if (token.status === 'match') {
    classes.push('border-slate-200 bg-white text-slate-700')
  } else if (token.status === 'remove') {
    classes.push(
      'border-rose-200 bg-rose-50 text-rose-700 line-through decoration-rose-500 decoration-2',
    )
  } else if (token.status === 'add') {
    classes.push('border-emerald-200 bg-emerald-50 text-emerald-700')
  } else {
    classes.push('border-amber-200 bg-amber-50 text-amber-700')
  }

  if (side === 'original') {
    const normalized = token.normalized
    if (props.nouns?.includes(normalized)) {
      classes.push('ring-1 ring-sky-200')
    } else if (props.verbs?.includes(normalized)) {
      classes.push('ring-1 ring-brand-accent/30')
    }
    classes.push('cursor-pointer hover:border-brand-accent hover:text-brand-accent')
  }

  return classes
}
</script>

<template>
  <section
    class="rounded-[2rem] border border-slate-200 bg-white p-4 shadow-mech"
    data-testid="transcription-result"
  >
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <div class="text-[10px] font-bold uppercase tracking-[0.32em] text-slate-400">
          Text Compare
        </div>
        <h3 class="mt-2 text-base font-semibold text-slate-900">
          原文 / 转写对照
        </h3>
      </div>

      <div class="flex items-center gap-2">
        <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
          {{ diffRows.counts.changed }} 处差异
        </span>
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-brand-accent hover:text-brand-accent"
          @click="emit('toggleTranslation')"
        >
          <Languages :size="14" />
          {{ showTranslation ? '隐藏中文' : '显示中文' }}
        </button>
      </div>
    </div>

    <div
      v-if="showTranslation"
      class="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-7 text-slate-600"
    >
      {{ translationLoading ? 'AI 翻译生成中...' : (translationText || '暂无翻译') }}
    </div>

    <div class="mt-4 grid gap-3">
      <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-3">
        <div class="mb-3 flex items-center justify-between gap-3">
          <span class="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">Original</span>
          <span class="text-xs text-slate-500">点击单词查看解释</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="token in diffRows.original"
            :key="`original-${token.index}-${token.raw}`"
            type="button"
            :class="tokenClasses(token, 'original')"
            @click="emit('wordClick', token.raw)"
          >
            {{ token.raw }}
          </button>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-slate-950/[0.03] p-3">
        <div class="mb-3 flex items-center justify-between gap-3">
          <span class="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">Transcript</span>
          <span class="text-xs text-slate-500">问题点时间戳只跳到用户录音</span>
        </div>
        <div
          v-if="diffRows.transcript.length > 0"
          class="flex flex-wrap gap-2"
        >
          <span
            v-for="token in diffRows.transcript"
            :key="`transcript-${token.index}-${token.raw}`"
            :class="tokenClasses(token, 'transcript')"
          >
            {{ token.raw }}
          </span>
        </div>
        <p
          v-else
          class="text-sm text-slate-500"
        >
          暂无转写
        </p>
      </div>
    </div>

    <div class="mt-4 flex flex-wrap gap-2 text-xs">
      <span class="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-rose-700">原文缺失</span>
      <span class="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-amber-700">替换表达</span>
      <span class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-emerald-700">转写新增</span>
    </div>
  </section>
</template>
