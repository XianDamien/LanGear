<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { TrendingUp } from 'lucide-vue-next'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, VisualMapComponent])

const props = defineProps<{
  data: { name: string; sentences: number }[]
}>()

const option = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#ffffff',
    borderColor: '#ff4d2d',
    textStyle: { color: '#0f172a', fontFamily: 'Source Sans 3' },
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    data: props.data.map((d) => d.name),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontFamily: 'Source Sans 3' },
  },
  yAxis: {
    type: 'value',
    show: false,
  },
  series: [
    {
      type: 'line',
      data: props.data.map((d) => d.sentences),
      smooth: true,
      showSymbol: false,
      lineStyle: { color: '#ff4d2d', width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255,77,45,0.35)' },
            { offset: 1, color: 'rgba(255,77,45,0)' },
          ],
        },
      },
    },
  ],
}))
</script>

<template>
  <div class="bg-brand-panel border border-slate-200 p-4 shadow-mech">
    <h3
      class="text-slate-500 uppercase mb-4 text-sm font-bold flex items-center gap-2"
    >
      <TrendingUp :size="16" />
      学习趋势
    </h3>
    <div class="h-48 w-full">
      <VChart :option="option" autoresize />
    </div>
  </div>
</template>
