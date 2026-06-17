<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Chart, PieController, ArcElement, Tooltip, Legend } from 'chart.js'
import { theme } from '../theme.js'

Chart.register(PieController, ArcElement, Tooltip, Legend)

function textColor() {
  return (
    getComputedStyle(document.documentElement).getPropertyValue('--text').trim() ||
    '#333'
  )
}

const props = defineProps({
  labels: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
})

const canvas = ref(null)
let chart = null

const PALETTE = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
  '#06b6d4', '#a855f7',
]

function render() {
  if (!canvas.value) return
  if (chart) chart.destroy()
  chart = new Chart(canvas.value, {
    type: 'pie',
    data: {
      labels: props.labels,
      datasets: [
        {
          data: props.values,
          backgroundColor: props.labels.map((_, i) => PALETTE[i % PALETTE.length]),
          borderWidth: 1,
          borderColor: '#fff',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: textColor() } },
        tooltip: {
          callbacks: {
            label(ctx) {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
              const val = ctx.parsed
              const pct = total ? ((val / total) * 100).toFixed(1) : 0
              return `${ctx.label}: ${val} (${pct}%)`
            },
          },
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
