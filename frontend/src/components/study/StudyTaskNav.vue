<script setup lang="ts">
import type { Card } from '@/types/domain'
import type { StudyTaskEntry } from '@/stores/studyTasks'

const props = defineProps<{
  cards: Card[]
  currentIndex: number
  taskMap: Record<string, StudyTaskEntry>
  collapsed?: boolean
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
  if (task.reviewStatus === 'failed') return task.errorCode || '失败'
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

function getStatusDetail(task: StudyTaskEntry | undefined): string | undefined {
  if (!task) return undefined
  if (task.reviewStatus === 'failed') {
    return [task.errorCode, task.errorMessage].filter(Boolean).join(': ')
  }
  return undefined
}

function getCardLabel(card: Card, index: number): string {
  return card.backText || card.frontText || `句子 ${index + 1}`
}
</script>

<template>
  <div
    :class="[
      'flex h-full min-h-0 flex-col rounded-[28px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(248,250,252,0.92))] p-3 shadow-mech',
      collapsed ? 'items-center px-2.5 py-3' : 'px-3 py-3.5',
    ]"
    :data-collapsed="collapsed ? 'true' : 'false'"
    data-testid="study-task-nav"
  >
    <div
      :class="[
        'flex w-full items-center border-b border-slate-200/80 pb-3',
        collapsed ? 'justify-center' : 'justify-between gap-3',
      ]"
    >
      <div :class="['min-w-0', collapsed ? 'text-center' : 'space-y-1']">
        <div class="text-[11px] font-bold uppercase tracking-[0.28em] text-slate-500">
          {{ collapsed ? '任务' : '句子任务导航' }}
        </div>
        <div v-if="!collapsed" class="text-xs text-slate-500">
          切卡不影响已提交任务状态
        </div>
      </div>

      <div
        v-if="!collapsed"
        class="inline-flex items-center rounded-full border border-slate-200 bg-white/80 px-2.5 py-1 font-pixel text-xs text-slate-600"
      >
        {{ cards.length }}
      </div>
    </div>

    <div :class="['mt-3 flex-1 overflow-y-auto', collapsed ? 'w-full' : 'pr-1']">
      <button
        v-for="(card, index) in cards"
        :key="card.id"
        :class="[
          'group relative w-full rounded-[22px] border text-left transition-all duration-200 ease-out',
          index === currentIndex
            ? 'border-brand-accent bg-white shadow-mech-sm ring-1 ring-brand-accent/15'
            : 'border-slate-200/90 bg-white/65 hover:border-brand-accent/50 hover:bg-white',
          collapsed ? 'mb-2 px-2 py-3 text-center last:mb-0' : 'mb-2 px-3 py-3.5 last:mb-0',
        ]"
        :title="[getCardLabel(card, index), getStatusLabel(getTask(card.id)), getStatusDetail(getTask(card.id))].filter(Boolean).join(' | ')"
        :data-testid="`task-nav-item-${index + 1}`"
        @click="emit('select', index)"
      >
        <div
          :class="[
            'flex items-center',
            collapsed ? 'justify-center gap-1.5' : 'justify-between gap-3',
          ]"
        >
          <div :class="['flex items-center', collapsed ? 'flex-col gap-1.5' : 'gap-2.5']">
            <span
              :class="[
                'inline-flex items-center justify-center rounded-full border font-pixel text-brand-accent',
                collapsed
                  ? 'h-9 w-9 text-sm'
                  : 'h-8 min-w-8 border-brand-accent/20 bg-brand-accent/5 px-2 text-sm',
              ]"
            >
              {{ index + 1 }}
            </span>
            <span
              v-if="!collapsed"
              class="max-w-[9.75rem] truncate text-xs uppercase tracking-[0.24em] text-slate-400"
            >
              Sentence
            </span>
          </div>

          <span
            :class="[
              'inline-flex h-2.5 w-2.5 rounded-full',
              getStatusClass(getTask(card.id)),
            ]"
          />
        </div>

        <div
          v-if="!collapsed"
          class="mt-3 truncate text-sm font-semibold text-slate-700"
        >
          {{ getCardLabel(card, index) }}
        </div>

        <div
          :class="[
            collapsed ? 'sr-only' : 'mt-1 text-xs text-slate-500',
          ]"
          :data-testid="`task-nav-status-${index + 1}`"
        >
          {{ getStatusLabel(getTask(card.id)) }}
        </div>

        <div
          v-if="!collapsed && getStatusDetail(getTask(card.id))"
          class="mt-2 truncate text-[11px] text-rose-600"
        >
          {{ getStatusDetail(getTask(card.id)) }}
        </div>

        <div
          v-if="index === currentIndex"
          class="absolute inset-y-3 left-0 w-1 rounded-r-full bg-brand-accent"
          aria-hidden="true"
        />
      </button>
    </div>
  </div>
</template>
