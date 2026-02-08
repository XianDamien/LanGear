import type { Rating, DailyStats, Deck, Card } from './domain'

export interface ApiError {
  code: string
  message: string
  request_id: string
}

export interface SubmitReviewRequest {
  lessonId: number
  cardId: number
  rating: Rating
  userAudio: string
  audioFormat: 'wav' | 'webm' | 'mp3'
}

export interface SubmitReviewResponse {
  reviewLogId: number
  resultType: 'single'
  transcription: string
  feedback: {
    pronunciation: string
    completeness: string
    fluency: string
    suggestions: string[]
    overallScore: number
  }
  srs: {
    state: string
    difficulty: number
    stability: number
    due: string
  }
}

export interface DashboardData {
  stats: {
    points: number
    reviewsPending: number
    streakDays: number
    dailyGoal: number
    dailyDone: number
    todayNew: number
    todayReview: number
    todayDone: number
  }
  weeklyTrend: { name: string; sentences: number }[]
  heatmap: DailyStats[]
}

export interface LessonSummary {
  lessonId: string
  overallScore: number
  overallComment: string
  frequentIssues: string[]
  improvements: string[]
  cardResults: {
    cardId: string
    score: number
    feedback: string
  }[]
}

export interface SettingsData {
  dailyNewLimit: number
  dailyReviewLimit: number
  defaultSourceScope: string
}

export interface DeckTreeResponse {
  tree: Deck[]
}

export interface LessonCardsResponse {
  lessonId: string
  lessonName: string
  cards: Card[]
}
