<script setup lang="ts">
import RetroButton from '@/components/ui/RetroButton.vue'
import type { Rating } from '@/types/domain'

defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  grade: [rating: Rating]
}>()

const buttons: { rating: Rating; label: string; interval: string; variant: 'danger' | 'secondary' | 'primary' | 'ghost'; extraClass?: string }[] = [
  { rating: 'again', label: '再来', interval: '1m', variant: 'danger' },
  { rating: 'hard', label: '困难', interval: '6m', variant: 'secondary' },
  { rating: 'good', label: '良好', interval: '10m', variant: 'primary' },
  { rating: 'easy', label: '轻松', interval: '4d', variant: 'ghost', extraClass: 'bg-blue-600 text-white hover:bg-blue-500' },
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
