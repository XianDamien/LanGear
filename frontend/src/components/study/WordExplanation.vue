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
  <div class="z-40 mt-4 w-full md:absolute md:bottom-6 md:right-6 md:mt-0 md:w-80">
    <RetroCard class="border-brand-accent bg-white shadow-xl" title="AI 解析">
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
