import type { Rating, DailyStats, Deck, Card } from './domain'

export interface ApiError {
  code: string
  message: string
  request_id: string
}

export interface STSToken {
  access_key_id: string
  access_key_secret: string
  security_token: string
  expiration: string
  bucket: string
  region: string
}

export type SubmissionStatus = 'processing' | 'completed' | 'failed'
export type ProgressState = 'asr_completed' | 'ai_processing'

export interface WordTimestamp {
  word: string
  start: number
  end: number
}

export interface TranscriptionResult {
  text: string
  timestamps: WordTimestamp[]
}

export interface FeedbackSuggestion {
  text: string
  target_word?: string
  timestamp?: number
}

export interface SubmitReviewRequest {
  lesson_id: number
  card_id: number
  rating: Rating
  oss_audio_path: string
}

export interface SubmitReviewResponseAsync {
  submission_id: number
  status: 'processing'
}

export interface PollingResponseProcessing {
  submission_id: number
  status: 'processing'
  progress?: ProgressState
}

export interface PollingResponseCompleted {
  submission_id: number
  status: 'completed'
  result_type: 'single'
  transcription: TranscriptionResult
  feedback: {
    pronunciation: string
    completeness: string
    fluency: string
    suggestions: FeedbackSuggestion[]
  }
  srs: {
    state: string
    difficulty: number
    stability: number
    due: string
  }
  oss_audio_path?: string | null
}

export interface PollingResponseFailed {
  submission_id: number
  status: 'failed'
  error_code: string
  error_message: string
}

export type PollingResponse =
  | PollingResponseProcessing
  | PollingResponseCompleted
  | PollingResponseFailed

/**
 * @deprecated 使用 SubmitReviewRequest (v2.0) 替代
 */
export interface SubmitReviewRequestV1 {
  lessonId: number
  cardId: number
  rating: Rating
  userAudio: string
  audioFormat: 'wav' | 'webm' | 'mp3'
}

/**
 * @deprecated 使用 PollingResponseCompleted (v2.0) 替代
 */
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
  tree?: Deck[]
  sources?: Array<{
    id: number
    title: string
    units: Array<{
      id: number
      title: string
      lessons: Array<{
        id: number
        title: string
        total_cards: number
        completed_cards: number
        due_cards: number
      }>
    }>
  }>
}

export interface LessonCardsResponse {
  lessonId: string
  lessonName: string
  cards: Card[]
}
