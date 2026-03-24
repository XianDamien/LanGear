<script setup lang="ts">
import RetroCard from '@/components/ui/RetroCard.vue'
import RetroButton from '@/components/ui/RetroButton.vue'

defineProps<{
  loading: boolean
  summaryText: string | null
}>()

const emit = defineEmits<{
  generate: []
  exit: []
}>()
</script>

<template>
  <div class="absolute inset-0 flex items-center justify-center bg-black/60 z-50">
    <RetroCard class="bg-white border-brand-accent w-full max-w-lg">
      <h3 class="text-xl font-bold text-brand-accent mb-2">
        本课完成
      </h3>
      <p class="text-slate-600 text-sm mb-4">
        是否生成本课的复述总结报告？
      </p>
      <p
        v-if="loading"
        class="text-slate-500 text-sm animate-pulse"
      >
        AI 总结生成中...
      </p>
      <p
        v-if="summaryText"
        class="text-slate-900 text-sm mb-4"
      >
        {{ summaryText }}
      </p>
      <div class="flex gap-2 justify-end">
        <RetroButton
          v-if="!summaryText"
          variant="primary"
          size="sm"
          :disabled="loading"
          @click="emit('generate')"
        >
          生成总结
        </RetroButton>
        <RetroButton
          variant="secondary"
          size="sm"
          @click="emit('exit')"
        >
          返回
        </RetroButton>
      </div>
    </RetroCard>
  </div>
</template>
