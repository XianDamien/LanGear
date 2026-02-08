import { computed, type Ref } from 'vue'
import type { DailyStats } from '@/types/domain'

export function useHeatmap(data: Ref<DailyStats[]>) {
  const chartData = computed(() =>
    data.value.map((d) => [d.date, d.count]),
  )

  const maxCount = computed(() =>
    Math.max(...data.value.map((d) => d.count), 1),
  )

  return { chartData, maxCount }
}
