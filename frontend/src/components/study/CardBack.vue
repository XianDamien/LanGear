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
    <!-- Target text with NLP highlighting -->
    <div class="bg-slate-50 p-6 border-l-4 border-brand-accent">
      <h2 class="text-3xl mb-2 tracking-wide">
        <HighlightedText
          :text="card.backText"
          :nouns="card.grammarInfo?.nouns"
          :verbs="card.grammarInfo?.verbs"
          @word-click="emit('wordClick', $event)"
        />
      </h2>
      <div class="mt-3">
        <RetroButton
          v-if="!showTranslation"
          variant="secondary"
          size="sm"
          @click="emit('showTranslation')"
        >
          显示中文翻译
        </RetroButton>
        <p v-else class="text-slate-500 italic text-lg">
          {{ translationLoading ? 'AI 翻译生成中...' : (card.backTranslation || '暂无翻译') }}
        </p>
      </div>
    </div>

    <!-- Audio comparison & AI feedback -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-white p-3 rounded text-sm border border-slate-200">
        <h3 class="text-slate-500 uppercase text-xs mb-2">音频对比</h3>
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-2">
            <RetroButton variant="secondary" size="sm" @click="emit('playOriginal')">
              原音频
            </RetroButton>
            <audio
              v-if="userAudioUrl"
              controls
              :src="userAudioUrl"
              class="h-8 w-full"
            />
            <span v-else class="text-slate-500 text-xs">暂无录音</span>
          </div>

          <!-- v2.0: 转写结果（支持时间戳跳转） -->
          <div class="mt-2">
            <div class="text-xs text-slate-500 uppercase mb-1">转写结果（点击跳转）</div>
            <div v-if="transcriptionTimestamps && transcriptionTimestamps.length > 0" class="flex flex-wrap">
              <TimestampWord
                v-for="(ts, idx) in transcriptionTimestamps"
                :key="idx"
                :timestamp="ts"
                @jump="emit('timestampJump', $event)"
              />
            </div>
            <div v-else class="text-brand-accent font-sans">
              {{ userTranscript || '暂无转写' }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white p-3 rounded text-sm relative border border-slate-200">
        <h3 class="text-slate-500 uppercase text-xs mb-1">AI 反馈</h3>

        <!-- v2.0 处理中状态 -->
        <div v-if="asyncSubmitState === 'processing'" class="animate-pulse space-y-2">
          <div class="h-4 bg-slate-200 rounded w-3/4"></div>
          <div class="h-4 bg-slate-200 rounded w-1/2"></div>
          <span class="text-slate-500 text-xs">AI 分析中...</span>
        </div>

        <!-- v2.0 完成状态（移除 overallScore） -->
        <template v-else-if="feedbackV2">
          <div class="space-y-2 text-xs">
            <p><strong>发音:</strong> {{ feedbackV2.feedback.pronunciation }}</p>
            <p><strong>完整度:</strong> {{ feedbackV2.feedback.completeness }}</p>
            <p><strong>流畅度:</strong> {{ feedbackV2.feedback.fluency }}</p>
            <!-- v2.0: 不再显示 overall_score -->

            <!-- 建议（支持时间戳跳转） -->
            <div v-if="feedbackV2.feedback.suggestions.length > 0" class="mt-2">
              <p class="font-semibold">建议:</p>
              <ul class="list-disc list-inside mt-1">
                <li
                  v-for="(suggestion, idx) in feedbackV2.feedback.suggestions"
                  :key="idx"
                  :class="[
                    suggestion.timestamp !== undefined &&
                      'cursor-pointer hover:text-brand-accent'
                  ]"
                  @click="handleSuggestionClick(suggestion)"
                >
                  {{ suggestion.text }}
                  <span v-if="suggestion.target_word" class="text-brand-accent">
                    ({{ suggestion.target_word }})
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </template>

        <!-- v1.x 兼容 -->
        <template v-else-if="feedbackLoading">
          <span class="animate-pulse text-slate-500">分析中...</span>
        </template>
        <template v-else-if="feedback">
          <p class="text-slate-900">{{ feedback.feedback.pronunciation }}</p>
          <p class="text-slate-600 text-xs mt-1">
            评分: <span class="font-pixel text-brand-accent">{{ feedback.feedback.overallScore }}</span>
          </p>
        </template>
        <span v-else class="text-slate-500">暂无反馈</span>
      </div>
    </div>

    <!-- Notes -->
    <div class="bg-white p-3 rounded text-sm border border-slate-200">
      <h3 class="text-slate-500 uppercase text-xs mb-2">笔记</h3>
      <textarea
        class="w-full border border-slate-200 p-2 text-slate-900 font-sans text-sm resize-none"
        placeholder="记录易错点或理解要点..."
        :value="notes"
        rows="3"
        @input="emit('update:notes', ($event.target as HTMLTextAreaElement).value)"
      />
    </div>

    <!-- FSRS grading -->
    <GradeButtons
      :disabled="submitState === 'submitting' || asyncSubmitState === 'processing'"
      @grade="emit('grade', $event)"
    />
  </div>
</template>
