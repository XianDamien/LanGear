<script setup lang="ts">
import RetroCard from '@/components/ui/RetroCard.vue'

defineProps<{
  word: string
  explanation: string
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <div class="absolute bottom-4 right-4 z-50 w-64">
    <RetroCard class="bg-white border-brand-accent" title="AI 解析">
      <div class="flex justify-between items-start mb-2">
        <span class="font-bold text-brand-accent text-xl">{{ word }}</span>
        <button
          class="text-slate-400 hover:text-slate-900"
          @click="emit('close')"
        >
          x
        </button>
      </div>
      <p class="text-sm leading-relaxed">{{ explanation }}</p>
    </RetroCard>
  </div>
</template>
