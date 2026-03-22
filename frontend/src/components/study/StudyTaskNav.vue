<script setup lang="ts">
import type { Card } from '@/types/domain'
import type { StudyTaskEntry } from '@/stores/studyTasks'

const props = defineProps<{
  cards: Card[]
  currentIndex: number
  taskMap: Record<string, StudyTaskEntry>
}>()

const emit = defineEmits<{
  select: [index: number]
}>()

function getTask(cardId: string) {
  return props.taskMap[cardId]
}

function getStatusLabel(task: StudyTaskEntry | undefined): string {
  if (!task) return '待练'
  if (task.reviewStatus === 'completed') return '完成'
  if (task.reviewStatus === 'failed') return '失败'
  if (task.reviewStatus === 'submitting' || task.reviewStatus === 'processing') return '评测中'
  if (task.uploadState === 'uploading') return '上传中'
  if (task.uploadState === 'failed') return '上传失败'
  if (task.uploadState === 'uploaded') return '已上传'
  return '待练'
}

function getStatusClass(task: StudyTaskEntry | undefined): string {
  if (!task) return 'bg-slate-300'
  if (task.reviewStatus === 'completed') return 'bg-emerald-500'
  if (task.reviewStatus === 'failed' || task.uploadState === 'failed') return 'bg-red-500'
  if (task.reviewStatus === 'submitting' || task.reviewStatus === 'processing') return 'bg-amber-500'
  if (task.uploadState === 'uploading') return 'bg-sky-500'
  if (task.uploadState === 'uploaded') return 'bg-brand-accent'
  return 'bg-slate-300'
}
</script>

<template>
  <div
    class="mb-4 rounded border border-slate-200 bg-brand-panel/90 p-3 shadow-mech-sm"
    data-testid="study-task-nav"
  >
    <div class="mb-2 flex items-center justify-between gap-3">
      <div class="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">句子任务导航</div>
      <div class="text-xs text-slate-500">切卡不影响已提交任务状态</div>
    </div>

    <div class="flex gap-2 overflow-x-auto pb-1">
      <button
        v-for="(card, index) in cards"
        :key="card.id"
        :class="[
          'group min-w-[7.5rem] rounded border px-3 py-2 text-left transition-colors',
          index === currentIndex
            ? 'border-brand-accent bg-white shadow-mech-sm'
            : 'border-slate-200 bg-white/70 hover:border-brand-accent/60',
        ]"
        :data-testid="`task-nav-item-${index + 1}`"
        @click="emit('select', index)"
      >
        <div class="mb-2 flex items-center justify-between gap-2">
          <span class="font-pixel text-sm text-brand-accent">{{ index + 1 }}</span>
          <span
            :class="[
              'inline-flex h-2.5 w-2.5 rounded-full',
              getStatusClass(getTask(card.id)),
            ]"
          />
        </div>
        <div class="truncate text-sm text-slate-700">
          {{ card.backText || card.frontText || `句子 ${index + 1}` }}
        </div>
        <div class="mt-1 text-xs text-slate-500" :data-testid="`task-nav-status-${index + 1}`">
          {{ getStatusLabel(getTask(card.id)) }}
        </div>
      </button>
    </div>
  </div>
</template>
