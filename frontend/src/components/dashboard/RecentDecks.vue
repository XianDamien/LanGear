<script setup lang="ts">
import { Play } from 'lucide-vue-next'
import type { Deck } from '@/types/domain'

defineProps<{
  decks: Deck[]
}>()

const emit = defineEmits<{
  play: [deckId: string]
}>()
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-4 uppercase text-brand-accent">
      学习中
    </h2>
    <div class="space-y-3">
      <div
        v-for="deck in decks"
        :key="deck.id"
        class="bg-white p-4 border border-slate-200 hover:border-brand-accent cursor-pointer transition-colors flex justify-between items-center group"
        @click="emit('play', deck.id)"
      >
        <div>
          <div class="font-bold text-lg group-hover:text-brand-accent">
            {{ deck.name }}
          </div>
          <div class="text-sm text-slate-500">
            <span class="font-pixel text-brand-accent">{{ deck.newCards }}</span>
            新卡 •
            <span class="font-pixel text-brand-accent">{{ deck.reviewCards }}</span>
            复习
          </div>
        </div>
        <Play
          class="text-slate-400 group-hover:text-brand-accent"
          fill="currentColor"
        />
      </div>
    </div>
  </div>
</template>
