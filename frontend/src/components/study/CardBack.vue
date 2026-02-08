<script setup lang="ts">
import RetroButton from '@/components/ui/RetroButton.vue'
import HighlightedText from './HighlightedText.vue'
import GradeButtons from './GradeButtons.vue'
import TimestampWord from './TimestampWord.vue'
import type { Card, Rating } from '@/types/domain'
import type {
  SubmitReviewResponse,
  PollingResponseCompleted,
  WordTimestamp,
  FeedbackSuggestion
} from '@/types/api'
import type { AsyncSubmitState } from '@/stores/study'

defineProps<{
  card: Card
  userTranscript: string
  userAudioUrl: string | null
  feedback: SubmitReviewResponse | null
  feedbackLoading: boolean
  showTranslation: boolean
  translationLoading: boolean
  notes: string
  submitState: string
  asyncSubmitState?: AsyncSubmitState
  feedbackV2?: PollingResponseCompleted | null
  transcriptionTimestamps?: WordTimestamp[]
}>()

const emit = defineEmits<{
  playOriginal: []
  showTranslation: []
  wordClick: [word: string]
  grade: [rating: Rating]
  'update:notes': [value: string]
  timestampJump: [timestamp: number]
}>()

function handleSuggestionClick(suggestion: FeedbackSuggestion) {
  if (suggestion.timestamp !== undefined) {
    emit('timestampJump', suggestion.timestamp)
  }
}
</script>

<template>
  <div class="w-full text-left space-y-6 animate-fadeIn">

    <!-- ROW 1: Audio Comparison Section -->
    <div class="bg-white p-4 rounded border border-slate-200">
      <h3 class="text-slate-500 uppercase text-xs mb-3 font-bold">音频对比</h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- LEFT: Original audio -->
        <div class="space-y-2">
          <div class="text-xs text-slate-600 font-semibold mb-1">原音频</div>
          <RetroButton variant="secondary" size="sm" @click="emit('playOriginal')">
            播放原音频
          </RetroButton>
        </div>

        <!-- RIGHT: User audio -->
        <div class="space-y-2">
          <div class="text-xs text-slate-600 font-semibold mb-1">你的录音</div>
          <audio
            v-if="userAudioUrl"
            controls
            :src="userAudioUrl"
            class="h-8 w-full"
          />
          <span v-else class="text-slate-500 text-xs">暂无录音</span>
        </div>
      </div>
    </div>

    <!-- ROW 2: Text Comparison -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

      <!-- LEFT: Original text + translation -->
      <div class="bg-slate-50 p-4 border-l-4 border-brand-accent rounded">
        <div class="text-xs text-slate-500 uppercase mb-2 font-bold">原文</div>
        <h2 class="text-2xl mb-3 tracking-wide leading-relaxed">
          <HighlightedText
            :text="card.backText"
            :nouns="card.grammarInfo?.nouns"
            :verbs="card.grammarInfo?.verbs"
            @word-click="emit('wordClick', $event)"
          />
        </h2>

        <div class="mt-3 pt-3 border-t border-slate-200">
          <RetroButton
            v-if="!showTranslation"
            variant="secondary"
            size="sm"
            @click="emit('showTranslation')"
          >
            显示中文翻译
          </RetroButton>
          <p v-else class="text-slate-600 italic text-base">
            {{ translationLoading ? 'AI 翻译生成中...' : (card.backTranslation || '暂无翻译') }}
          </p>
        </div>
      </div>

      <!-- RIGHT: ASR transcription -->
      <div class="bg-white p-4 border border-slate-200 rounded">
        <div class="text-xs text-slate-500 uppercase mb-2 font-bold">你的转写结果</div>

        <!-- Timestamp words -->
        <div v-if="transcriptionTimestamps?.length" class="flex flex-wrap gap-1">
          <TimestampWord
            v-for="(ts, idx) in transcriptionTimestamps"
            :key="idx"
            :timestamp="ts"
            @jump="emit('timestampJump', $event)"
          />
        </div>

        <!-- Fallback: plain text -->
        <div v-else class="text-brand-accent font-sans text-lg">
          {{ userTranscript || '暂无转写' }}
        </div>

        <div class="mt-2 text-xs text-slate-500">
          点击词语可跳转到对应时间点
        </div>
      </div>
    </div>

    <!-- ROW 3: AI Feedback (centered) -->
    <div class="bg-white p-5 rounded border border-slate-200">
      <h3 class="text-slate-500 uppercase text-xs mb-3 font-bold">AI 评测反馈</h3>

      <!-- Processing state -->
      <div v-if="asyncSubmitState === 'processing'" class="animate-pulse space-y-2">
        <div class="h-4 bg-slate-200 rounded w-3/4"></div>
        <div class="h-4 bg-slate-200 rounded w-1/2"></div>
        <span class="text-slate-500 text-xs">AI 分析中...</span>
      </div>

      <!-- v2.0 completed state -->
      <template v-else-if="feedbackV2">
        <div class="space-y-3 text-sm max-w-2xl mx-auto">
          <!-- Feedback grid -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div class="bg-slate-50 p-3 rounded">
              <div class="text-xs text-slate-500 uppercase mb-1">发音</div>
              <p class="text-slate-900">{{ feedbackV2.feedback.pronunciation }}</p>
            </div>
            <div class="bg-slate-50 p-3 rounded">
              <div class="text-xs text-slate-500 uppercase mb-1">完整度</div>
              <p class="text-slate-900">{{ feedbackV2.feedback.completeness }}</p>
            </div>
            <div class="bg-slate-50 p-3 rounded">
              <div class="text-xs text-slate-500 uppercase mb-1">流畅度</div>
              <p class="text-slate-900">{{ feedbackV2.feedback.fluency }}</p>
            </div>
          </div>

          <!-- Suggestions -->
          <div v-if="feedbackV2.feedback.suggestions.length > 0"
               class="bg-amber-50 p-3 rounded border-l-4 border-amber-400">
            <p class="font-semibold text-amber-900 mb-2 text-sm">改进建议:</p>
            <ul class="list-disc list-inside space-y-1">
              <li
                v-for="(suggestion, idx) in feedbackV2.feedback.suggestions"
                :key="idx"
                :class="[
                  'text-sm text-amber-900',
                  suggestion.timestamp !== undefined &&
                    'cursor-pointer hover:text-brand-accent hover:underline'
                ]"
                @click="handleSuggestionClick(suggestion)"
              >
                {{ suggestion.text }}
                <span v-if="suggestion.target_word" class="font-semibold text-brand-accent">
                  ({{ suggestion.target_word }})
                </span>
              </li>
            </ul>
          </div>
        </div>
      </template>

      <!-- v1.x compatibility -->
      <template v-else-if="feedbackLoading">
        <span class="animate-pulse text-slate-500 text-center block">AI 分析中...</span>
      </template>
      <template v-else-if="feedback">
        <div class="max-w-2xl mx-auto">
          <p class="text-slate-900 mb-2">{{ feedback.feedback.pronunciation }}</p>
          <p class="text-slate-600 text-sm">
            评分: <span class="font-pixel text-brand-accent text-lg">
              {{ feedback.feedback.overallScore }}
            </span>
          </p>
        </div>
      </template>
      <span v-else class="text-slate-500 text-center block">暂无反馈</span>
    </div>

    <!-- ROW 4: Notes -->
    <div class="bg-white p-4 rounded border border-slate-200">
      <h3 class="text-slate-500 uppercase text-xs mb-2 font-bold">学习笔记</h3>
      <textarea
        class="w-full border border-slate-200 rounded p-3 text-slate-900 font-sans text-sm resize-none focus:border-brand-accent focus:outline-none focus:ring-2 focus:ring-brand-accent/20"
        placeholder="记录易错点或理解要点..."
        :value="notes"
        rows="3"
        @input="emit('update:notes', ($event.target as HTMLTextAreaElement).value)"
      />
    </div>

    <!-- ROW 5: Grade Buttons -->
    <GradeButtons
      :disabled="submitState === 'submitting' || asyncSubmitState === 'processing'"
      @grade="emit('grade', $event)"
    />
  </div>
</template>
