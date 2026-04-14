<script setup lang="ts">
import type { PollingResponseCompleted, FeedbackSuggestion, FeedbackIssue } from '@/types/api'

const props = defineProps<{
  feedback: PollingResponseCompleted | null
  loading: boolean
  errorCode?: string | null
  errorMessage?: string | null
}>()

const emit = defineEmits<{
  timestampClick: [timestamp: number]
}>()

function handleSuggestionClick(suggestion: FeedbackSuggestion) {
  if (suggestion.timestamp != null) {
    emit('timestampClick', suggestion.timestamp)
  }
}

function handleIssueClick(issue: FeedbackIssue) {
  if (issue.timestamp != null) {
    emit('timestampClick', issue.timestamp)
  }
}
</script>

<template>
  <div
    class="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-mech"
    data-testid="feedback-panel"
  >
    <h3 class="mb-3 text-xs font-bold uppercase text-slate-500">
      AI 评测反馈
    </h3>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="animate-pulse space-y-2"
      data-testid="feedback-processing"
    >
      <div class="h-4 w-3/4 rounded bg-slate-200" />
      <div class="h-4 w-1/2 rounded bg-slate-200" />
      <span class="text-xs text-slate-500">AI 分析中...</span>
    </div>

    <!-- Error State -->
    <div
      v-else-if="errorCode || errorMessage"
      class="rounded border-l-4 border-rose-400 bg-rose-50 p-4 text-sm"
    >
      <p class="font-semibold text-rose-900">
        {{ errorCode || 'SUBMISSION_FAILED' }}
      </p>
      <p class="mt-2 text-rose-800">
        {{ errorMessage || '提交失败，请重试' }}
      </p>
    </div>

    <!-- Feedback Content -->
    <template v-else-if="feedback">
      <div class="mx-auto max-w-2xl space-y-3 text-sm">
        <div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div class="rounded bg-slate-50 p-3">
            <div class="mb-1 text-xs uppercase text-slate-500">发音</div>
            <p class="text-slate-900">{{ feedback.feedback.pronunciation }}</p>
          </div>
          <div class="rounded bg-slate-50 p-3">
            <div class="mb-1 text-xs uppercase text-slate-500">完整度</div>
            <p class="text-slate-900">{{ feedback.feedback.completeness }}</p>
          </div>
          <div class="rounded bg-slate-50 p-3">
            <div class="mb-1 text-xs uppercase text-slate-500">流畅度</div>
            <p class="text-slate-900">{{ feedback.feedback.fluency }}</p>
          </div>
        </div>

        <!-- Suggestions -->
        <div
          v-if="feedback.feedback.suggestions.length > 0"
          class="rounded border-l-4 border-amber-400 bg-amber-50 p-3"
        >
          <p class="mb-2 text-sm font-semibold text-amber-900">改进建议:</p>
          <ul class="list-inside list-disc space-y-1">
            <li
              v-for="(suggestion, idx) in feedback.feedback.suggestions"
              :key="idx"
              :class="[
                'text-sm text-amber-900',
                suggestion.timestamp != null && 'cursor-pointer hover:text-brand-accent hover:underline'
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

        <!-- Issues -->
        <div
          v-if="feedback.feedback.issues.length > 0"
          class="rounded border-l-4 border-rose-400 bg-rose-50 p-3"
        >
          <p class="mb-2 text-sm font-semibold text-rose-900">问题点:</p>
          <ul class="list-inside list-disc space-y-1">
            <li
              v-for="(issue, idx) in feedback.feedback.issues"
              :key="idx"
              :class="[
                'text-sm text-rose-900',
                issue.timestamp != null && 'cursor-pointer hover:text-brand-accent hover:underline'
              ]"
              @click="handleIssueClick(issue)"
            >
              {{ issue.problem }}
            </li>
          </ul>
        </div>
      </div>
    </template>

    <!-- Empty State -->
    <span v-else class="block text-center text-slate-500">暂无反馈</span>
  </div>
</template>
