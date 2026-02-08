import http from '../http'
import type { LessonSummary } from '@/types/api'

export function fetchLessonSummary(lessonId: string) {
  return http.get<LessonSummary>(`/decks/${lessonId}/summary`)
}
