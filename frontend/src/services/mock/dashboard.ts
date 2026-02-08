import type { DashboardData } from '@/types/api'

export const mockDashboardData: DashboardData = {
  stats: {
    points: 1240,
    reviewsPending: 14,
    streakDays: 5,
    dailyGoal: 30,
    dailyDone: 15,
    todayNew: 5,
    todayReview: 10,
    todayDone: 15,
  },
  weeklyTrend: [
    { name: '周一', sentences: 12 },
    { name: '周二', sentences: 18 },
    { name: '周三', sentences: 5 },
    { name: '周四', sentences: 25 },
    { name: '周五', sentences: 30 },
    { name: '周六', sentences: 45 },
    { name: '周日', sentences: 10 },
  ],
  heatmap: Array.from({ length: 90 }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (89 - i))
    return {
      date: d.toISOString().slice(0, 10),
      count: Math.floor(Math.random() * 50),
    }
  }),
}
