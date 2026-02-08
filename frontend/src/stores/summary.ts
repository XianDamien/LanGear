import { ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchLessonSummary } from '@/services/api/summary'
import type { LessonSummary } from '@/types/api'

export const useSummaryStore = defineStore('summary', () => {
  const summaryData = ref<LessonSummary | null>(null)
  const loading = ref(false)
  const error = ref(false)

  async function load(lessonId: string) {
    loading.value = true
    error.value = false
    try {
      const { data } = await fetchLessonSummary(lessonId)
      summaryData.value = data
    } catch {
      error.value = true
    } finally {
      loading.value = false
    }
  }

  return { summaryData, loading, error, load }
})
