export interface Deck {
  id: string
  name: string
  description: string
  totalCards: number
  newCards: number
  reviewCards: number
  completedCards: number
  parentId?: string
  children?: Deck[]
  type: 'source' | 'unit' | 'lesson'
}

export interface Card {
  id: string
  frontAudio?: string
  frontText?: string
  backText: string
  backTranslation: string
  notes?: string
  difficulty: number
  grammarInfo?: {
    nouns: string[]
    verbs: string[]
  }
}

export type Rating = 'again' | 'hard' | 'good' | 'easy'

export interface DailyStats {
  date: string
  count: number
}

export interface StudySessionResult {
  cardId: string
  rating: Rating
  userAudioBlob?: Blob
  responseTime: number
}
