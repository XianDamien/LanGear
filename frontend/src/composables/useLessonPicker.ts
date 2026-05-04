import { computed, ref, type Ref } from 'vue'
import type { Deck } from '@/types/domain'
import {
  buildLessonSelectionItems,
  collectLessonIds,
  findDeckContext,
} from '@/utils/deckSelection'

interface UseLessonPickerOptions {
  deckTree: Ref<Deck[]>
  selectedLessonIds: Ref<number[]>
  replaceLessons: (lessonIds: number[]) => Promise<number[]>
}

export function useLessonPicker(options: UseLessonPickerOptions) {
  const pickerDeckId = ref<string | null>(null)

  const pickerContext = computed(() =>
    pickerDeckId.value ? findDeckContext(options.deckTree.value, pickerDeckId.value) : null,
  )
  const pickerDeck = computed(() => pickerContext.value?.deck ?? null)
  const pickerLessons = computed(() =>
    pickerContext.value
      ? buildLessonSelectionItems(
          pickerContext.value.deck,
          pickerContext.value.sourceTitle,
          pickerContext.value.unitTitle,
        )
      : [],
  )
  const pickerSelectedLessonIds = computed(() => {
    if (!pickerDeck.value) return []

    const lessonIdSet = new Set(collectLessonIds(pickerDeck.value))
    return options.selectedLessonIds.value.filter((lessonId) => lessonIdSet.has(lessonId))
  })

  function openPicker(deckId: string) {
    pickerDeckId.value = deckId
  }

  function closePicker() {
    pickerDeckId.value = null
  }

  async function savePickerSelection(lessonIds: number[]) {
    if (!pickerDeck.value) return []

    const lessonIdSet = new Set(collectLessonIds(pickerDeck.value))
    const nextLessonIds = options.selectedLessonIds.value.filter(
      (lessonId) => !lessonIdSet.has(lessonId),
    )
    const updatedLessonIds = await options.replaceLessons([...nextLessonIds, ...lessonIds])
    closePicker()
    return updatedLessonIds
  }

  return {
    pickerDeck,
    pickerLessons,
    pickerSelectedLessonIds,
    openPicker,
    closePicker,
    savePickerSelection,
  }
}
