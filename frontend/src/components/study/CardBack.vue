<script setup lang="ts">
import RetroButton from '@/components/ui/RetroButton.vue'
import HighlightedText from './HighlightedText.vue'
import GradeButtons from './GradeButtons.vue'
import type { Card, Rating } from '@/types/domain'
import type { SubmitReviewResponse } from '@/types/api'

const props = defineProps<{
  card: Card
  userTranscript: string
  userAudioUrl: string | null
  feedback: SubmitReviewResponse | null
  feedbackLoading: boolean
  showTranslation: boolean
  translationLoading: boolean
  notes: string
  submitState: string
}>()

const emit = defineEmits<{
  playOriginal: []
  showTranslation: []
  wordClick: [word: string]
  grade: [rating: Rating]
  'update:notes': [value: string]
}>()
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
          v-if="!props.showTranslation"
          variant="secondary"
          size="sm"
          @click="emit('showTranslation')"
        >
          显示中文翻译
        </RetroButton>
        <p v-else class="text-slate-500 italic text-lg">
          {{ props.translationLoading ? 'AI 翻译生成中...' : (card.backTranslation || '暂无翻译') }}
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
          <div class="text-brand-accent font-sans">
            {{ userTranscript || '暂无转写' }}
          </div>
        </div>
      </div>

      <div class="bg-white p-3 rounded text-sm relative border border-slate-200">
        <h3 class="text-slate-500 uppercase text-xs mb-1">AI 反馈</h3>
        <span v-if="feedbackLoading" class="animate-pulse text-slate-500">
          分析中...
        </span>
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
      :disabled="submitState === 'submitting'"
      @grade="emit('grade', $event)"
    />
  </div>
</template>
