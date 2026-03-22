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
  variant: 'danger' | 'secondary' | 'primary' | 'ghost'
  extraClass?: string
}[] = [
  { rating: 1, label: '再来', interval: '1m', variant: 'danger' },
  { rating: 2, label: '困难', interval: '6m', variant: 'secondary' },
  { rating: 3, label: '良好', interval: '10m', variant: 'primary' },
  { rating: 4, label: '轻松', interval: '4d', variant: 'ghost', extraClass: 'bg-blue-600 text-white hover:bg-blue-500' },
]
</script>

<template>
  <div class="mt-2 grid grid-cols-2 gap-2 md:grid-cols-4">
    <RetroButton
      v-for="btn in buttons"
      :key="btn.rating"
      :variant="btn.variant"
      size="sm"
      :class="btn.extraClass"
      :disabled="disabled"
      @click="emit('grade', btn.rating)"
    >
      <div class="flex min-w-0 flex-col text-center">
        <span>{{ btn.label }}</span>
        <span class="font-pixel text-xs text-slate-600">{{ btn.interval }}</span>
      </div>
    </RetroButton>
  </div>
</template>
