import { ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDeckTree } from '@/services/api/decks'
import type { Deck } from '@/types/domain'

export const useDeckStore = defineStore('deck', () => {
  const deckTree = ref<Deck[]>([])
  const selectedSourceId = ref<string | null>(null)
  const selectedLessonId = ref<string | null>(null)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const { data } = await fetchDeckTree()
      deckTree.value = data.tree
    } finally {
      loading.value = false
    }
  }

  function selectLesson(lessonId: string) {
    selectedLessonId.value = lessonId
  }

  return { deckTree, selectedSourceId, selectedLessonId, loading, load, selectLesson }
})
