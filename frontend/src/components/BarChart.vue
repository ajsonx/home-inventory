<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js'
import { theme } from '../theme.js'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

function cssVar(name, fallback) {
  return (
    getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
  )
}

const props = defineProps({
  labels: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  // 数值前缀（如货币符号），用于 tooltip 与坐标轴
  unit: { type: String, default: '' },
  horizontal: { type: Boolean, default: true },
})

const canvas = ref(null)
let chart = null

const PALETTE = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
  '#06b6d4', '#a855f7',
]

function fmt(v) {
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function render() {
  if (!canvas.value) return
  if (chart) chart.destroy()
  const tColor = cssVar('--text', '#333')
  const gridColor = cssVar('--border', '#e5e7eb')
  chart = new Chart(canvas.value, {
    type: 'bar',
    data: {
      labels: props.labels,
      datasets: [
        {
          data: props.values,
          backgroundColor: props.labels.map((_, i) => PALETTE[i % PALETTE.length]),
          borderRadius: 6,
        },
      ],
    },
    options: {
      indexAxis: props.horizontal ? 'y' : 'x',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${props.unit}${fmt(ctx.parsed[props.horizontal ? 'x' : 'y'])}`,
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: tColor,
            callback: (val) => (props.horizontal ? `${props.unit}${val}` : val),
          },
          grid: { color: gridColor },
        },
        y: {
          ticks: {
            color: tColor,
            callback: function (val) {
              const label = this.getLabelForValue(val)
              return props.horizontal ? label : `${props.unit}${val}`
            },
          },
          grid: { color: gridColor },
        },
      },
    },
  })
}

onMounted(render)
watch(() => [props.labels, props.values, theme.value], render, { deep: true })
onBeforeUnmount(() => {
  if (chart) chart.destroy()
})
</script>

<template>
  <div class="chart-box">
    <canvas ref="canvas"></canvas>
  </div>
</template>
