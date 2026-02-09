import { ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDeckTree } from '@/services/api/decks'
import type { Deck } from '@/types/domain'

interface BackendLesson {
  id: number
  title: string
  total_cards: number
  completed_cards: number
  due_cards: number
}

interface BackendUnit {
  id: number
  title: string
  lessons: BackendLesson[]
}

interface BackendSource {
  id: number
  title: string
  units: BackendUnit[]
}

function transformSources(sources: BackendSource[]): Deck[] {
  return sources.map((source) => ({
    id: String(source.id),
    name: source.title,
    description: '',
    type: 'source' as const,
    totalCards: source.units.reduce((sum, u) => sum + u.lessons.reduce((s, l) => s + l.total_cards, 0), 0),
    newCards: source.units.reduce((sum, u) => sum + u.lessons.reduce((s, l) => s + (l.total_cards - l.completed_cards), 0), 0),
    reviewCards: source.units.reduce((sum, u) => sum + u.lessons.reduce((s, l) => s + l.due_cards, 0), 0),
    completedCards: source.units.reduce((sum, u) => sum + u.lessons.reduce((s, l) => s + l.completed_cards, 0), 0),
    children: source.units.map((unit) => ({
      id: String(unit.id),
      name: unit.title,
      description: '',
      type: 'unit' as const,
      parentId: String(source.id),
      totalCards: unit.lessons.reduce((s, l) => s + l.total_cards, 0),
      newCards: unit.lessons.reduce((s, l) => s + (l.total_cards - l.completed_cards), 0),
      reviewCards: unit.lessons.reduce((s, l) => s + l.due_cards, 0),
      completedCards: unit.lessons.reduce((s, l) => s + l.completed_cards, 0),
      children: unit.lessons.map((lesson) => ({
        id: String(lesson.id),
        name: lesson.title,
        description: '',
        type: 'lesson' as const,
        parentId: String(unit.id),
        totalCards: lesson.total_cards,
        newCards: lesson.total_cards - lesson.completed_cards,
        reviewCards: lesson.due_cards,
        completedCards: lesson.completed_cards,
      })),
    })),
  }))
}

export const useDeckStore = defineStore('deck', () => {
  const deckTree = ref<Deck[]>([])
  const selectedSourceId = ref<string | null>(null)
  const selectedLessonId = ref<string | null>(null)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const { data } = await fetchDeckTree()
      // Real API returns { sources: [...] }, mock returns { tree: [...] }
      if (data.sources) {
        deckTree.value = transformSources(data.sources)
      } else if (data.tree) {
        deckTree.value = data.tree
      }
    } finally {
      loading.value = false
    }
  }

  function selectLesson(lessonId: string) {
    selectedLessonId.value = lessonId
  }

  return { deckTree, selectedSourceId, selectedLessonId, loading, load, selectLesson }
})
