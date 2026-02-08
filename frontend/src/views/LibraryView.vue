<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useDeckStore } from '@/stores/deck'
import DeckTreeItem from '@/components/library/DeckTreeItem.vue'

const router = useRouter()
const deckStore = useDeckStore()
const { deckTree, loading } = storeToRefs(deckStore)

onMounted(() => {
  if (!deckTree.value.length) {
    deckStore.load()
  }
})

function handleSelectLesson(lessonId: string) {
  deckStore.selectLesson(lessonId)
  router.push(`/study/${lessonId}`)
}
</script>

<template>
  <div class="animate-fadeIn">
    <h2 class="text-3xl font-bold mb-6 text-brand-accent uppercase">题库</h2>

    <div v-if="loading" class="text-center text-slate-500 py-20">加载中...</div>

    <div v-else class="space-y-2">
      <DeckTreeItem
        v-for="deck in deckTree"
        :key="deck.id"
        :deck="deck"
        :depth="0"
        @select-lesson="handleSelectLesson"
      />
    </div>
  </div>
</template>
