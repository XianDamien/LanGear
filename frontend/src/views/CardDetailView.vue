<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import RetroCard from '@/components/ui/RetroCard.vue'
import RetroButton from '@/components/ui/RetroButton.vue'

const router = useRouter()

const detail = ref({
  pronunciation: '发音整体清晰，注意连读部分的自然衔接。',
  completeness: '内容完整，未遗漏关键信息。',
  fluency: '语速适中，部分句末有停顿。',
  suggestions: [
    '注意 "the" 在元音前的发音变化',
    '尝试更自然的语调起伏',
    '连读处可以更流畅',
  ],
  overallScore: 82,
})
</script>

<template>
  <div class="animate-fadeIn max-w-2xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-3xl font-bold text-brand-accent uppercase">
        AI 反馈详情
      </h2>
      <RetroButton
        variant="ghost"
        size="sm"
        @click="router.back()"
      >
        返回
      </RetroButton>
    </div>

    <div class="space-y-4">
      <RetroCard title="发音准确度">
        <p class="text-slate-900">
          {{ detail.pronunciation }}
        </p>
      </RetroCard>

      <RetroCard title="内容完整度">
        <p class="text-slate-900">
          {{ detail.completeness }}
        </p>
      </RetroCard>

      <RetroCard title="流畅度">
        <p class="text-slate-900">
          {{ detail.fluency }}
        </p>
      </RetroCard>

      <RetroCard title="改进建议">
        <ul class="list-disc list-inside space-y-1">
          <li
            v-for="(s, i) in detail.suggestions"
            :key="i"
            class="text-slate-700"
          >
            {{ s }}
          </li>
        </ul>
      </RetroCard>

      <RetroCard title="综合评分">
        <div class="text-4xl font-bold font-pixel text-brand-accent">
          {{ detail.overallScore }}
        </div>
      </RetroCard>
    </div>
  </div>
</template>
