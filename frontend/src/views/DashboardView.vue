<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useDashboardStore } from '@/stores/dashboard'
import { useDeckStore } from '@/stores/deck'
import StatsCards from '@/components/dashboard/StatsCards.vue'
import ActivityChart from '@/components/dashboard/ActivityChart.vue'
import RecentDecks from '@/components/dashboard/RecentDecks.vue'
import Leaderboard from '@/components/dashboard/Leaderboard.vue'

const router = useRouter()
const dashboardStore = useDashboardStore()
const deckStore = useDeckStore()
const { stats, weeklyTrend, loading } = storeToRefs(dashboardStore)
const { deckTree } = storeToRefs(deckStore)

onMounted(() => {
  dashboardStore.load()
  deckStore.load()
})

function handlePlayDeck(deckId: string) {
  // Find a lesson under this deck to start studying
  function findFirstLesson(decks: typeof deckTree.value): string | null {
    for (const d of decks) {
      if (d.type === 'lesson') return d.id
      if (d.children?.length) {
        const found = findFirstLesson(d.children)
        if (found) return found
      }
    }
    return null
  }

  const target = deckTree.value.find((d) => d.id === deckId)
  if (target) {
    const lessonId = target.type === 'lesson' ? target.id : findFirstLesson(target.children || [])
    if (lessonId) {
      router.push(`/study/${lessonId}`)
    }
  }
}
</script>

<template>
  <div class="space-y-6 animate-fadeIn">
    <div v-if="loading" class="text-center text-slate-500 py-20">加载中...</div>
    <template v-else-if="stats">
      <StatsCards :stats="stats" />
      <ActivityChart :data="weeklyTrend" />
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RecentDecks :decks="deckTree" @play="handlePlayDeck" />
        <Leaderboard />
      </div>
    </template>
  </div>
</template>
