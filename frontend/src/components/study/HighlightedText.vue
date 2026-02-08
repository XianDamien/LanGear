<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  text: string
  nouns?: string[]
  verbs?: string[]
}>()

const emit = defineEmits<{
  wordClick: [word: string]
}>()

const words = computed(() => {
  return props.text.split(' ').map((word) => {
    const clean = word.replace(/[.,!?]/g, '').toLowerCase()
    let highlight = ''
    if (props.nouns?.includes(clean)) highlight = 'noun-highlight'
    else if (props.verbs?.includes(clean)) highlight = 'verb-highlight'
    return { word, highlight }
  })
})
</script>

<template>
  <span
    v-for="(item, i) in words"
    :key="i"
    :class="[
      item.highlight,
      'mr-2 inline-block cursor-help hover:scale-105 transition-transform',
    ]"
    title="点击查看 AI 解析"
    @click="emit('wordClick', item.word)"
  >
    {{ item.word }}
  </span>
</template>
