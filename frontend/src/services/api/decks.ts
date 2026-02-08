import http from '../http'
import type { DeckTreeResponse, LessonCardsResponse } from '@/types/api'

export function fetchDeckTree() {
  return http.get<DeckTreeResponse>('/decks/tree')
}

export function fetchLessonCards(lessonId: string) {
  return http.get<LessonCardsResponse>(`/decks/${lessonId}/cards`)
}
