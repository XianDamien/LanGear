<script setup lang="ts">
import RetroButton from '@/components/ui/RetroButton.vue'
import HighlightedText from './HighlightedText.vue'
import GradeButtons from './GradeButtons.vue'
import type { Card, FsrsRating } from '@/types/domain'
import type {
  SubmitReviewResponse,
  PollingResponseCompleted,
  FeedbackSuggestion,
  FeedbackIssue,
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
  errorCode?: string | null
  errorMessage?: string | null
}>()

const emit = defineEmits<{
  playOriginal: []
  showTranslation: []
  wordClick: [word: string]
  grade: [rating: FsrsRating]
  'update:notes': [value: string]
  timestampJump: [timestamp: number]
}>()

function handleSuggestionClick(suggestion: FeedbackSuggestion) {
  if (suggestion.timestamp != null) {
    emit('timestampJump', suggestion.timestamp)
  }
}

function handleIssueClick(issue: FeedbackIssue) {
  if (issue.timestamp != null) {
    emit('timestampJump', issue.timestamp)
  }
}
</script>

<template>
  <div class="flex h-full min-h-0 w-full flex-col text-left animate-fadeIn" data-testid="card-back">
    <div class="flex-1 min-h-0 space-y-6 overflow-y-auto pr-1 sm:pr-2">

      <!-- ROW 1: Audio Comparison Section -->
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 text-xs font-bold uppercase text-slate-500">音频对比</h3>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <!-- LEFT: Original audio -->
          <div class="space-y-2">
            <div class="mb-1 text-xs font-semibold text-slate-600">原音频</div>
            <RetroButton variant="secondary" size="sm" @click="emit('playOriginal')">
              播放原音频
            </RetroButton>
          </div>

          <!-- RIGHT: User audio -->
          <div class="space-y-2">
            <div class="mb-1 text-xs font-semibold text-slate-600">你的录音</div>
            <audio
              v-if="userAudioUrl"
              controls
              :src="userAudioUrl"
              class="h-8 w-full"
            />
            <span v-else class="text-xs text-slate-500">暂无录音</span>
          </div>
        </div>
      </div>

      <!-- ROW 2: Text Comparison -->
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">

        <!-- LEFT: Original text + translation -->
        <div class="rounded border-l-4 border-brand-accent bg-slate-50 p-4">
          <div class="mb-2 text-xs font-bold uppercase text-slate-500">原文</div>
          <h2 class="mb-3 text-xl leading-relaxed tracking-wide sm:text-2xl">
            <HighlightedText
              :text="card.backText"
              :nouns="card.grammarInfo?.nouns"
              :verbs="card.grammarInfo?.verbs"
              @word-click="emit('wordClick', $event)"
            />
          </h2>

          <div class="mt-3 border-t border-slate-200 pt-3">
            <RetroButton
              v-if="!showTranslation"
              variant="secondary"
              size="sm"
              @click="emit('showTranslation')"
            >
              显示中文翻译
            </RetroButton>
            <p v-else class="text-base italic text-slate-600">
              {{ translationLoading ? 'AI 翻译生成中...' : (card.backTranslation || '暂无翻译') }}
            </p>
          </div>
        </div>

        <!-- RIGHT: Display transcription -->
        <div class="rounded border border-slate-200 bg-white p-4" data-testid="transcription-result">
          <div class="mb-2 text-xs font-bold uppercase text-slate-500">你的转写结果</div>

          <div class="text-lg leading-relaxed text-brand-accent">
            {{ userTranscript || '暂无转写' }}
          </div>

          <div class="mt-2 text-xs text-slate-500">
            跳转回听请使用下方问题点或改进建议中的时间定位
          </div>
        </div>
      </div>

      <!-- ROW 3: AI Feedback (centered) -->
      <div class="rounded border border-slate-200 bg-white p-5" data-testid="feedback-panel">
        <h3 class="mb-3 text-xs font-bold uppercase text-slate-500">AI 评测反馈</h3>

        <!-- Processing state -->
        <div
          v-if="asyncSubmitState === 'processing'"
          class="animate-pulse space-y-2"
          data-testid="feedback-processing"
        >
          <div class="h-4 w-3/4 rounded bg-slate-200"></div>
          <div class="h-4 w-1/2 rounded bg-slate-200"></div>
          <span class="text-xs text-slate-500">AI 分析中...</span>
        </div>

        <div
          v-else-if="asyncSubmitState === 'failed'"
          class="rounded border-l-4 border-rose-400 bg-rose-50 p-4 text-sm"
        >
          <p class="font-semibold text-rose-900">
            {{ errorCode || 'SUBMISSION_FAILED' }}
          </p>
          <p class="mt-2 text-rose-800">
            {{ errorMessage || '提交失败，请重试' }}
          </p>
        </div>

        <!-- v2.0 completed state -->
        <template v-else-if="feedbackV2">
          <div class="mx-auto max-w-2xl space-y-3 text-sm">
            <!-- Feedback grid -->
            <div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
              <div class="rounded bg-slate-50 p-3">
                <div class="mb-1 text-xs uppercase text-slate-500">发音</div>
                <p class="text-slate-900">{{ feedbackV2.feedback.pronunciation }}</p>
              </div>
              <div class="rounded bg-slate-50 p-3">
                <div class="mb-1 text-xs uppercase text-slate-500">完整度</div>
                <p class="text-slate-900">{{ feedbackV2.feedback.completeness }}</p>
              </div>
              <div class="rounded bg-slate-50 p-3">
                <div class="mb-1 text-xs uppercase text-slate-500">流畅度</div>
                <p class="text-slate-900">{{ feedbackV2.feedback.fluency }}</p>
              </div>
            </div>

            <!-- Suggestions -->
            <div
              v-if="feedbackV2.feedback.suggestions.length > 0"
              class="rounded border-l-4 border-amber-400 bg-amber-50 p-3"
            >
              <p class="mb-2 text-sm font-semibold text-amber-900">改进建议:</p>
              <ul class="list-inside list-disc space-y-1">
                <li
                  v-for="(suggestion, idx) in feedbackV2.feedback.suggestions"
                  :key="idx"
                  :class="[
                    'text-sm text-amber-900',
                    suggestion.timestamp != null &&
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

            <div
              v-if="feedbackV2.feedback.issues.length > 0"
              class="rounded border-l-4 border-rose-400 bg-rose-50 p-3"
            >
              <p class="mb-2 text-sm font-semibold text-rose-900">问题点:</p>
              <ul class="list-inside list-disc space-y-1">
                <li
                  v-for="(issue, idx) in feedbackV2.feedback.issues"
                  :key="idx"
                  :class="[
                    'text-sm text-rose-900',
                    issue.timestamp != null &&
                      'cursor-pointer hover:text-brand-accent hover:underline'
                  ]"
                  @click="handleIssueClick(issue)"
                >
                  {{ issue.problem }}
                </li>
              </ul>
            </div>
          </div>
        </template>

        <!-- v1.x compatibility -->
        <template v-else-if="feedbackLoading">
          <span class="block animate-pulse text-center text-slate-500">AI 分析中...</span>
        </template>
        <template v-else-if="feedback">
          <div class="mx-auto max-w-2xl">
            <p class="mb-2 text-slate-900">{{ feedback.feedback.pronunciation }}</p>
            <p class="text-sm text-slate-600">
              评分: <span class="font-pixel text-lg text-brand-accent">
                {{ feedback.feedback.overallScore }}
              </span>
            </p>
          </div>
        </template>
        <span v-else class="block text-center text-slate-500">暂无反馈</span>
      </div>

      <!-- ROW 4: Notes -->
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-2 text-xs font-bold uppercase text-slate-500">学习笔记</h3>
        <textarea
          class="w-full resize-none rounded border border-slate-200 p-3 text-sm text-slate-900 focus:border-brand-accent focus:outline-none focus:ring-2 focus:ring-brand-accent/20"
          placeholder="记录易错点或理解要点..."
          :value="notes"
          rows="3"
          @input="emit('update:notes', ($event.target as HTMLTextAreaElement).value)"
        />
      </div>
    </div>

    <!-- ROW 5: Grade Buttons -->
    <div class="mt-4 border-t border-slate-200/80 pt-4">
      <GradeButtons
        :disabled="
          submitState === 'submitting' ||
          asyncSubmitState === 'processing' ||
          asyncSubmitState === 'submitting' ||
          asyncSubmitState === 'failed' ||
          asyncSubmitState === 'idle'
        "
        @grade="emit('grade', $event)"
      />
    </div>
  </div>
</template>
