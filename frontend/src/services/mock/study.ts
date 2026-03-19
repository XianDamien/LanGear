import type { SubmitReviewResponse } from '@/types/api'

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
