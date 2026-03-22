import type { FsrsRating, RatingLabel, CardState } from '@/types/domain'
import type {
  StudySessionCardResponse,
  StudySessionResponse,
  SubmitReviewResponse,
} from '@/types/api'
import { mockLessonCards } from './decks'

const ratingLabelMap: Record<FsrsRating, RatingLabel> = {
  1: 'again',
  2: 'hard',
  3: 'good',
  4: 'easy',
}

const lessonSourceScope: Record<number, number[]> = {
  1: [1],
  2: [1],
  3: [1],
  4: [2],
}

function formatShanghaiIso(rawDate: Date): string {
  const shifted = new Date(rawDate.getTime() + 8 * 60 * 60 * 1000)
  return shifted.toISOString().replace('Z', '+08:00')
}

function buildMockCardState(index: number): CardState {
  const states: CardState[] = ['learning', 'review', 'new', 'relearning']
  return states[index % states.length]!
}

function buildSessionCards(lessonId: number): StudySessionCardResponse[] {
  const lessonKey = `l${lessonId}`
  const lesson = mockLessonCards[lessonKey]
  if (!lesson) return []

  return lesson.cards.map((card, index) => ({
    id: card.id,
    lesson_id: lessonId,
    card_index: index + 1,
    front_text: card.backText,
    back_text: card.backTranslation,
    audio_path: card.frontAudio ?? '',
    oss_audio_path: card.ossAudioPath ?? null,
    card_state: buildMockCardState(index),
    due_at:
      index % 2 === 0
        ? formatShanghaiIso(new Date(Date.now() + (index + 1) * 60 * 60 * 1000))
        : null,
  }))
}

export function buildMockStudySession(lessonId?: number): StudySessionResponse {
  const resolvedLessonId = lessonId && mockLessonCards[`l${lessonId}`] ? lessonId : 1
  const cards = buildSessionCards(resolvedLessonId)
  const reviewCards = cards.filter((card) => card.card_state !== 'new')
  const newCards = cards.filter((card) => card.card_state === 'new')

  return {
    server_time: formatShanghaiIso(new Date()),
    session_date: formatShanghaiIso(new Date()).slice(0, 10),
    scope: {
      lesson_id: resolvedLessonId,
      source_ids: lessonSourceScope[resolvedLessonId] ?? [1],
    },
    quota: {
      daily_new_limit: 10,
      daily_review_limit: 20,
      new_used: 0,
      review_used: 0,
      new_remaining: Math.max(0, 10 - newCards.length),
      review_remaining: Math.max(0, 20 - reviewCards.length),
    },
    summary: {
      new_remaining: Math.max(0, 10 - newCards.length),
      review_remaining: Math.max(0, 20 - reviewCards.length),
      due_count: reviewCards.filter((card) => card.due_at).length,
    },
    lesson_name: mockLessonCards[`l${resolvedLessonId}`]?.lessonName ?? '学习任务',
    cards,
  }
}

export function getMockRatingLabel(rating: FsrsRating): RatingLabel {
  return ratingLabelMap[rating]
}

export function buildMockRatingSrs(rating: FsrsRating) {
  const nextDueHours: Record<FsrsRating, number> = {
    1: 0.5,
    2: 6,
    3: 24,
    4: 96,
  }

  return {
    state: rating === 1 ? 'learning' : 'review',
    difficulty: rating === 1 ? 0.72 : rating === 2 ? 0.56 : rating === 3 ? 0.41 : 0.28,
    stability: rating === 1 ? 0.4 : rating === 2 ? 2.1 : rating === 3 ? 5.8 : 9.4,
    due_at: formatShanghaiIso(
      new Date(Date.now() + nextDueHours[rating] * 60 * 60 * 1000),
    ),
  }
}

export function mockSubmitReview(_cardId: string, userTranscript: string): SubmitReviewResponse {
  return {
    reviewLogId: Math.floor(Math.random() * 10000),
    resultType: 'single',
    transcription: userTranscript || '',
    feedback: {
      pronunciation: '发音整体清晰，注意连读部分的自然衔接。',
      completeness: '内容完整，未遗漏关键信息。',
      fluency: '语速适中，部分句末有停顿。',
      suggestions: [
        '注意 "the" 在元音前的发音变化',
        '尝试更自然的语调起伏',
        '连读处可以更流畅',
      ],
      overallScore: 75 + Math.floor(Math.random() * 20),
    },
    srs: {
      state: 'review',
      difficulty: 0.3,
      stability: 5.0,
      due: new Date(Date.now() + 86400000 * 3).toISOString(),
    },
  }
}
