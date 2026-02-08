<script setup lang="ts">
import { computed } from 'vue'
import type { WordTimestamp } from '@/types/api'

const props = defineProps<{
  timestamp: WordTimestamp
  isActive?: boolean
}>()

const emit = defineEmits<{
  jump: [timestamp: number]
}>()

const displayTime = computed(() => {
  const sec = props.timestamp.start
  return `${Math.floor(sec)}s`
})
</script>

<template>
  <span
    :class="[
      'inline-block px-2 py-1 mr-1 mb-1 rounded cursor-pointer transition-all',
      'border border-slate-300 hover:border-brand-accent hover:bg-brand-accent/10',
      isActive && 'border-brand-accent bg-brand-accent/20'
    ]"
    :title="`点击跳转到 ${displayTime}`"
    @click="emit('jump', timestamp.start)"
  >
    {{ timestamp.word }}
    <span class="text-xs text-slate-500 ml-1">{{ displayTime }}</span>
  </span>
</template>
