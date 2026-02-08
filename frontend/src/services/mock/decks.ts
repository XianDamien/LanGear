import type { Deck } from '@/types/domain'
import type { DeckTreeResponse, LessonCardsResponse } from '@/types/api'

const mockTree: Deck[] = [
  {
    id: 's1',
    name: '新概念英语 2',
    description: '经典教材',
    totalCards: 96,
    newCards: 5,
    reviewCards: 12,
    completedCards: 79,
    type: 'source',
    children: [
      {
        id: 'u1',
        name: 'Unit 1 - 基础篇',
        description: '',
        totalCards: 48,
        newCards: 3,
        reviewCards: 8,
        completedCards: 37,
        type: 'unit',
        parentId: 's1',
        children: [
          {
            id: 'l1',
            name: 'Lesson 1 - A private conversation',
            description: '',
            totalCards: 6,
            newCards: 2,
            reviewCards: 3,
            completedCards: 1,
            type: 'lesson',
            parentId: 'u1',
          },
          {
            id: 'l2',
            name: 'Lesson 2 - Breakfast or lunch?',
            description: '',
            totalCards: 5,
            newCards: 1,
            reviewCards: 2,
            completedCards: 2,
            type: 'lesson',
            parentId: 'u1',
          },
        ],
      },
      {
        id: 'u2',
        name: 'Unit 2 - 进阶篇',
        description: '',
        totalCards: 48,
        newCards: 2,
        reviewCards: 4,
        completedCards: 42,
        type: 'unit',
        parentId: 's1',
        children: [
          {
            id: 'l3',
            name: 'Lesson 3 - Please send me a card',
            description: '',
            totalCards: 4,
            newCards: 0,
            reviewCards: 2,
            completedCards: 2,
            type: 'lesson',
            parentId: 'u2',
          },
        ],
      },
    ],
  },
  {
    id: 's2',
    name: '雅思听力 第1章',
    description: '剑桥雅思',
    totalCards: 40,
    newCards: 10,
    reviewCards: 0,
    completedCards: 30,
    type: 'source',
    children: [
      {
        id: 'u3',
        name: 'Section 1',
        description: '',
        totalCards: 20,
        newCards: 5,
        reviewCards: 0,
        completedCards: 15,
        type: 'unit',
        parentId: 's2',
        children: [
          {
            id: 'l4',
            name: 'Test 1 - Part 1',
            description: '',
            totalCards: 10,
            newCards: 3,
            reviewCards: 0,
            completedCards: 7,
            type: 'lesson',
            parentId: 'u3',
          },
        ],
      },
    ],
  },
]

export const mockDeckTree: DeckTreeResponse = { tree: mockTree }

export const mockLessonCards: Record<string, LessonCardsResponse> = {
  l1: {
    lessonId: 'l1',
    lessonName: 'Lesson 1 - A private conversation',
    cards: [
      {
        id: 'c1',
        frontAudio: '',
        backText: 'The quick brown fox jumps over the lazy dog.',
        backTranslation: '这只敏捷的棕色狐狸跳过了懒惰的狗。',
        difficulty: 1,
        grammarInfo: { nouns: ['fox', 'dog'], verbs: ['jumps'] },
      },
      {
        id: 'c2',
        frontAudio: '',
        backText: 'Learning a language requires patience and practice.',
        backTranslation: '学习语言需要耐心和练习。',
        difficulty: 2,
        grammarInfo: {
          nouns: ['language', 'patience', 'practice'],
          verbs: ['requires', 'learning'],
        },
      },
    ],
  },
  l2: {
    lessonId: 'l2',
    lessonName: 'Lesson 2 - Breakfast or lunch?',
    cards: [
      {
        id: 'c3',
        frontAudio: '',
        backText: 'It was Sunday and I never get up early on Sundays.',
        backTranslation: '那是星期天，我星期天从不早起。',
        difficulty: 1,
        grammarInfo: { nouns: ['sunday', 'sundays'], verbs: ['get'] },
      },
      {
        id: 'c4',
        frontAudio: '',
        backText: 'I sometimes stay in bed until lunchtime.',
        backTranslation: '有时候我会在床上待到午饭时间。',
        difficulty: 1,
        grammarInfo: { nouns: ['bed', 'lunchtime'], verbs: ['stay'] },
      },
    ],
  },
  l3: {
    lessonId: 'l3',
    lessonName: 'Lesson 3 - Please send me a card',
    cards: [
      {
        id: 'c5',
        frontAudio: '',
        backText: 'Postcards always spoil my holidays.',
        backTranslation: '明信片总是破坏我的假期。',
        difficulty: 2,
        grammarInfo: { nouns: ['postcards', 'holidays'], verbs: ['spoil'] },
      },
    ],
  },
  l4: {
    lessonId: 'l4',
    lessonName: 'Test 1 - Part 1',
    cards: [
      {
        id: 'c6',
        frontAudio: '',
        backText: 'Good morning, I would like to book a room please.',
        backTranslation: '早上好，我想预订一个房间。',
        difficulty: 1,
        grammarInfo: { nouns: ['morning', 'room'], verbs: ['book'] },
      },
    ],
  },
}
