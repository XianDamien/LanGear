<script setup lang="ts">
import RetroButton from '@/components/ui/RetroButton.vue'
import type { FsrsRating } from '@/types/domain'

defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  grade: [rating: FsrsRating]
}>()

const buttons: {
  rating: FsrsRating
  label: string
  interval: string
  hint: string
  variant: 'danger' | 'secondary' | 'primary' | 'success'
  chipClass: string
}[] = [
  {
    rating: 1,
    label: '再来',
    interval: '1m',
    hint: '立即重练',
    variant: 'danger',
    chipClass: 'bg-white/15 text-white',
  },
  {
    rating: 2,
    label: '困难',
    interval: '6m',
    hint: '短间隔回顾',
    variant: 'secondary',
    chipClass: 'bg-slate-900/5 text-slate-700',
  },
  {
    rating: 3,
    label: '良好',
    interval: '10m',
    hint: '标准复习节奏',
    variant: 'primary',
    chipClass: 'bg-white/15 text-white',
  },
  {
    rating: 4,
    label: '轻松',
    interval: '4d',
    hint: '拉开下次间隔',
    variant: 'success',
    chipClass: 'bg-white/15 text-white',
  },
]
</script>

<template>
  <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
    <RetroButton
      v-for="btn in buttons"
      :key="btn.rating"
      :variant="btn.variant"
      size="sm"
      class="h-full min-h-[4.75rem] items-stretch px-3 py-3 text-left"
      :disabled="disabled"
      @click="emit('grade', btn.rating)"
    >
      <div class="flex w-full min-w-0 flex-col gap-2">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-semibold tracking-[0.16em] sm:text-[0.95rem]">
            {{ btn.label }}
          </span>
          <span
            :class="[
              'font-pixel rounded-full px-2 py-1 text-[0.7rem] tracking-[0.08em]',
              btn.chipClass,
            ]"
          >
            {{ btn.interval }}
          </span>
        </div>
        <span class="text-[0.68rem] tracking-[0.12em] opacity-80">
          {{ btn.hint }}
        </span>
      </div>
    </RetroButton>
  </div>
</template>
