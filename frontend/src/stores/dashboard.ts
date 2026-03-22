import { ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDashboard } from '@/services/api/dashboard'
import type { DashboardData } from '@/types/api'
import type { DailyStats } from '@/types/domain'

interface LegacyDashboardData {
  today: {
    new_limit: number
    review_limit: number
    completed: number
  }
  streak_days: number
  heatmap: DailyStats[]
}

function isLegacyDashboardData(data: DashboardData | LegacyDashboardData): data is LegacyDashboardData {
  return 'today' in data && 'streak_days' in data
}

function formatWeeklyTrendDate(date: string): string {
  const parsed = new Date(`${date}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return date.slice(5)
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][parsed.getDay()] || date.slice(5)
}

function normalizeDashboardData(data: DashboardData | LegacyDashboardData): DashboardData {
  if (!isLegacyDashboardData(data)) {
    return data
  }

  const dailyDone = data.today.completed
  const dailyGoal = data.today.new_limit + data.today.review_limit
  const todayNew = Math.min(dailyDone, data.today.new_limit)
  const todayReview = Math.max(dailyDone - todayNew, 0)
  const weeklyTrend = data.heatmap.slice(-7).map((entry) => ({
    name: formatWeeklyTrendDate(entry.date),
    sentences: entry.count,
  }))

  return {
    stats: {
      points: dailyDone,
      reviewsPending: Math.max(data.today.review_limit - todayReview, 0),
      streakDays: data.streak_days,
      dailyGoal,
      dailyDone,
      todayNew,
      todayReview,
      todayDone: dailyDone,
    },
    weeklyTrend,
    heatmap: data.heatmap,
  }
}

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardData['stats'] | null>(null)
  const weeklyTrend = ref<{ name: string; sentences: number }[]>([])
  const heatmap = ref<DailyStats[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load() {
    loading.value = true
    error.value = null
    try {
      const { data } = await fetchDashboard()
      const normalized = normalizeDashboardData(data as DashboardData | LegacyDashboardData)
      stats.value = normalized.stats
      weeklyTrend.value = normalized.weeklyTrend
      heatmap.value = normalized.heatmap
    } catch (err) {
      const message = err instanceof Error ? err.message : '加载首页数据失败'
      error.value = message
      stats.value = null
      weeklyTrend.value = []
      heatmap.value = []
    } finally {
      loading.value = false
    }
  }

  return { stats, weeklyTrend, heatmap, loading, error, load }
})
