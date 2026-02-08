import type { LessonSummary } from '@/types/api'

export function mockLessonSummary(lessonId: string): LessonSummary {
  return {
    lessonId,
    overallScore: 82,
    overallComment: '本课表现良好。建议重点关注发音连读与动词时态变化，并回听不顺畅的句子。',
    frequentIssues: [
      '连读不够自然',
      '部分元音发音不准确',
      '句尾语调偏平',
    ],
    improvements: [
      '多听原音频并模仿语调',
      '注意功能词的弱读',
      '练习长句的换气节奏',
    ],
    cardResults: [
      { cardId: 'c1', score: 85, feedback: '发音清晰，语速适中' },
      { cardId: 'c2', score: 78, feedback: '注意 "requires" 的重音位置' },
    ],
  }
}
