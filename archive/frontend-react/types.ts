export interface Deck {
  id: string;
  name: string;
  description: string;
  totalCards: number;
  newCards: number;
  reviewCards: number;
  parentId?: string; // For nesting (Book -> Unit -> Lesson)
  children?: Deck[];
  type: 'folder' | 'deck';
}

export interface Card {
  id: string;
  frontAudio?: string; // URL or base64
  frontText?: string; // Hidden initially
  backText: string;
  backTranslation: string;
  notes?: string;
  difficulty: number;
  grammarInfo?: {
    nouns: string[];
    verbs: string[];
  };
}

export enum FSRSGrade {
  Again = 1,
  Hard = 2,
  Good = 3,
  Easy = 4
}

export interface DailyStats {
  date: string;
  count: number;
}

export interface StudySessionResult {
  cardId: string;
  grade: FSRSGrade;
  userAudioBlob?: Blob;
  responseTime: number;
}