<script setup lang="ts">
import { ref } from 'vue'
import { ChevronRight, ChevronDown, Play } from 'lucide-vue-next'
import RetroButton from '@/components/ui/RetroButton.vue'
import type { Deck } from '@/types/domain'

const props = defineProps<{
  deck: Deck
  depth?: number
}>()

const emit = defineEmits<{
  selectLesson: [lessonId: string]
}>()

const expanded = ref(props.depth === 0)

function toggle() {
  if (props.deck.children?.length) {
    expanded.value = !expanded.value
  }
}
</script>

<template>
  <div :style="{ paddingLeft: `${(depth ?? 0) * 16}px` }">
    <div
      :class="[
        'flex items-center justify-between p-3 border border-slate-200 mb-2 transition-colors',
        deck.type === 'lesson'
          ? 'hover:border-brand-accent cursor-pointer bg-white'
          : 'bg-slate-50 cursor-pointer hover:bg-slate-100',
      ]"
      @click="deck.type === 'lesson' ? emit('selectLesson', deck.id) : toggle()"
    >
      <div class="flex items-center gap-2">
        <template v-if="deck.children?.length">
          <ChevronDown v-if="expanded" :size="16" class="text-slate-400" />
          <ChevronRight v-else :size="16" class="text-slate-400" />
        </template>
        <div v-else class="w-4" />

        <div>
          <div class="font-bold" :class="deck.type === 'lesson' ? 'text-base' : 'text-lg'">
            {{ deck.name }}
          </div>
          <div v-if="deck.type === 'lesson'" class="text-sm text-slate-500">
            <span class="font-pixel text-brand-accent">{{ deck.newCards }}</span> 新卡 •
            <span class="font-pixel text-brand-accent">{{ deck.reviewCards }}</span> 复习 •
            <span class="font-pixel text-green-600">{{ deck.completedCards }}</span> 已完成
          </div>
          <div v-else class="text-xs text-slate-500 uppercase">
            {{ deck.totalCards }} 句
          </div>
        </div>
      </div>

      <RetroButton
        v-if="deck.type === 'lesson'"
        size="sm"
        variant="secondary"
        @click.stop="emit('selectLesson', deck.id)"
      >
        <Play :size="14" />
      </RetroButton>
    </div>

    <template v-if="expanded && deck.children?.length">
      <DeckTreeItem
        v-for="child in deck.children"
        :key="child.id"
        :deck="child"
        :depth="(depth ?? 0) + 1"
        @select-lesson="emit('selectLesson', $event)"
      />
    </template>
  </div>
</template>
