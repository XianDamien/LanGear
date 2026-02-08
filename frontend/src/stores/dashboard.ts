import { ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDashboard } from '@/services/api/dashboard'
import type { DashboardData } from '@/types/api'
import type { DailyStats } from '@/types/domain'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardData['stats'] | null>(null)
  const weeklyTrend = ref<{ name: string; sentences: number }[]>([])
  const heatmap = ref<DailyStats[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const { data } = await fetchDashboard()
      stats.value = data.stats
      weeklyTrend.value = data.weeklyTrend
      heatmap.value = data.heatmap
    } finally {
      loading.value = false
    }
  }

  return { stats, weeklyTrend, heatmap, loading, load }
})
