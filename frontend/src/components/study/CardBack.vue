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
  <div class="flex h-full min-h-0 w-full flex-col gap-4 text-left animate-fadeIn" data-testid="card-back">
    <div class="flex-1 min-h-0 overflow-y-auto pr-1 pb-1 sm:pr-2">
      <div class="grid content-start gap-4 sm:gap-5">
        <div class="rounded-[26px] border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-4 shadow-mech-sm sm:p-5">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="font-pixel text-[0.72rem] tracking-[0.18em] text-brand-accent">AUDIO CHECK</p>
              <h3 class="mt-2 text-lg font-semibold text-slate-900">对照原音与本次录音</h3>
            </div>
            <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-[0.68rem] tracking-[0.16em] text-slate-500">
              回听对比
            </span>
          </div>

          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="rounded-[22px] border border-slate-200 bg-white/90 p-4">
              <div class="mb-3 text-xs font-semibold tracking-[0.16em] text-slate-600">原音频</div>
              <RetroButton variant="secondary" size="sm" class="w-full" @click="emit('playOriginal')">
                播放原音频
              </RetroButton>
            </div>

            <div class="rounded-[22px] border border-slate-200 bg-white/90 p-4">
              <div class="mb-3 text-xs font-semibold tracking-[0.16em] text-slate-600">你的录音</div>
              <audio
                v-if="userAudioUrl"
                controls
                :src="userAudioUrl"
                class="h-10 w-full"
              />
              <span v-else class="text-xs text-slate-500">暂无录音</span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div class="rounded-[26px] border border-brand-accent/15 bg-[linear-gradient(180deg,rgba(255,77,45,0.06)_0%,rgba(248,250,252,0.85)_100%)] p-4 sm:p-5">
            <div class="mb-2 text-xs font-bold tracking-[0.18em] text-slate-500">原文</div>
            <h2 class="mb-3 text-xl leading-relaxed tracking-wide text-slate-900 sm:text-2xl">
              <HighlightedText
                :text="card.backText"
                :nouns="card.grammarInfo?.nouns"
                :verbs="card.grammarInfo?.verbs"
                @word-click="emit('wordClick', $event)"
              />
            </h2>

            <div class="mt-4 border-t border-slate-200 pt-4">
              <RetroButton
                v-if="!showTranslation"
                variant="secondary"
                size="sm"
                @click="emit('showTranslation')"
              >
                显示中文翻译
              </RetroButton>
              <p v-else class="text-base italic leading-7 text-slate-600">
                {{ translationLoading ? 'AI 翻译生成中...' : (card.backTranslation || '暂无翻译') }}
              </p>
            </div>
          </div>

          <div
            class="rounded-[26px] border border-slate-200 bg-slate-950 p-4 text-white shadow-[0_20px_50px_rgba(15,23,42,0.16)] sm:p-5"
            data-testid="transcription-result"
          >
            <div class="mb-2 text-xs font-bold tracking-[0.18em] text-white/55">你的转写结果</div>
            <div class="rounded-[22px] border border-white/10 bg-white/5 p-4">
              <div class="text-lg leading-relaxed text-white/95">
                {{ userTranscript || '暂无转写' }}
              </div>
            </div>
            <div class="mt-3 text-xs tracking-[0.14em] text-white/55">
              可在下方问题点或改进建议中点击时间定位，回听对应片段
            </div>
          </div>
        </div>

        <div class="rounded-[26px] border border-slate-200 bg-white p-5 shadow-mech-sm" data-testid="feedback-panel">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="font-pixel text-[0.72rem] tracking-[0.18em] text-brand-accent">AI FEEDBACK</p>
              <h3 class="mt-2 text-lg font-semibold text-slate-900">评测反馈</h3>
            </div>
            <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[0.68rem] tracking-[0.16em] text-slate-500">
              {{ asyncSubmitState === 'completed' ? '已完成' : asyncSubmitState === 'failed' ? '失败' : '处理中' }}
            </span>
          </div>

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
            class="rounded-[20px] border border-rose-200 bg-rose-50 p-4 text-sm"
          >
            <p class="font-semibold text-rose-900">
              {{ errorCode || 'SUBMISSION_FAILED' }}
            </p>
            <p class="mt-2 text-rose-800">
              {{ errorMessage || '提交失败，请重试' }}
            </p>
          </div>

          <template v-else-if="feedbackV2">
            <div class="space-y-4 text-sm">
              <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
                <div class="rounded-[20px] bg-slate-50 p-4">
                  <div class="mb-1 text-xs uppercase tracking-[0.16em] text-slate-500">发音</div>
                  <p class="text-slate-900">{{ feedbackV2.feedback.pronunciation }}</p>
                </div>
                <div class="rounded-[20px] bg-slate-50 p-4">
                  <div class="mb-1 text-xs uppercase tracking-[0.16em] text-slate-500">完整度</div>
                  <p class="text-slate-900">{{ feedbackV2.feedback.completeness }}</p>
                </div>
                <div class="rounded-[20px] bg-slate-50 p-4">
                  <div class="mb-1 text-xs uppercase tracking-[0.16em] text-slate-500">流畅度</div>
                  <p class="text-slate-900">{{ feedbackV2.feedback.fluency }}</p>
                </div>
              </div>

              <div
                v-if="feedbackV2.feedback.suggestions.length > 0"
                class="rounded-[20px] border border-amber-200 bg-amber-50 p-4"
              >
                <p class="mb-2 text-sm font-semibold text-amber-900">改进建议</p>
                <ul class="list-inside list-disc space-y-1.5">
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
                class="rounded-[20px] border border-rose-200 bg-rose-50 p-4"
              >
                <p class="mb-2 text-sm font-semibold text-rose-900">问题点</p>
                <ul class="list-inside list-disc space-y-1.5">
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

        <div class="rounded-[26px] border border-slate-200 bg-white p-4 shadow-mech-sm">
          <h3 class="mb-2 text-xs font-bold tracking-[0.18em] text-slate-500">学习笔记</h3>
          <textarea
            class="w-full resize-none rounded-[20px] border border-slate-200 p-3 text-sm text-slate-900 focus:border-brand-accent focus:outline-none focus:ring-2 focus:ring-brand-accent/20"
            placeholder="记录易错点或理解要点..."
            :value="notes"
            rows="3"
            @input="emit('update:notes', ($event.target as HTMLTextAreaElement).value)"
          />
        </div>
      </div>
    </div>

    <div class="shrink-0 rounded-[26px] border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-4 shadow-mech-sm sm:p-5">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="font-pixel text-[0.72rem] tracking-[0.18em] text-brand-accent">FSRS RATING</p>
          <h3 class="mt-2 text-lg font-semibold text-slate-900">选择本次复习结果</h3>
        </div>
        <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[0.68rem] tracking-[0.16em] text-slate-500">
          AI 完成后可用
        </span>
      </div>

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
