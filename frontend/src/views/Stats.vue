<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'
import PieChart from '../components/PieChart.vue'
import BarChart from '../components/BarChart.vue'

const router = useRouter()
const data = ref(null)
const selectedLocation = ref('')
const locationItems = ref([])

const globalLabels = computed(() =>
  data.value ? Object.keys(data.value.category_counts) : [],
)
const globalValues = computed(() =>
  data.value ? Object.values(data.value.category_counts) : [],
)

function fmtMoney(v) {
  return Number(v || 0).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

// 金额对比：按金额从高到低排序的分类
const amountRows = computed(() => {
  if (!data.value) return []
  const amount = data.value.category_amount || {}
  const counts = data.value.category_counts || {}
  return Object.keys(amount)
    .map((cat) => ({ cat, amount: amount[cat] || 0, count: counts[cat] || 0 }))
    .sort((a, b) => b.amount - a.amount)
})
const amountLabels = computed(() => amountRows.value.map((r) => r.cat))
const amountValues = computed(() => amountRows.value.map((r) => r.amount))
const hasAmount = computed(() => amountValues.value.some((v) => v > 0))

const locations = computed(() =>
  data.value ? Object.keys(data.value.location_counts) : [],
)

const locLabels = computed(() => {
  if (!data.value || !selectedLocation.value) return []
  return Object.keys(data.value.location_category[selectedLocation.value] || {})
})
const locValues = computed(() => {
  if (!data.value || !selectedLocation.value) return []
  return Object.values(data.value.location_category[selectedLocation.value] || {})
})

async function load() {
  try {
    data.value = await api.stats()
  } catch (e) {
    if (e.code === 401) router.push({ name: 'login' })
  }
}

async function selectLocation(loc) {
  selectedLocation.value = loc
  locationItems.value = await api.listItems({ location: loc })
}

onMounted(load)
</script>

<template>
  <div class="container">
    <div v-if="!data" class="empty">加载中...</div>
    <template v-else>
      <div class="chart-card">
        <h3>各分类占比（共 {{ data.total }} 件物品）</h3>
        <PieChart v-if="globalLabels.length" :labels="globalLabels" :values="globalValues" />
        <div v-else class="empty">暂无数据</div>
      </div>

      <div class="chart-card">
        <h3>各分类金额对比（总金额 CNY {{ fmtMoney(data.total_amount) }}）</h3>
        <BarChart
          v-if="hasAmount"
          :labels="amountLabels"
          :values="amountValues"
          unit="¥"
          :horizontal="true"
        />
        <div v-else class="empty">暂无金额数据（在物品中填写购入价格后显示）</div>

        <div v-if="amountRows.length" class="amount-table">
          <div class="amount-row amount-head">
            <span>分类</span>
            <span>数量</span>
            <span>总金额</span>
          </div>
          <div v-for="row in amountRows" :key="row.cat" class="amount-row">
            <span>{{ row.cat }}</span>
            <span>{{ row.count }}</span>
            <span>{{ fmtMoney(row.amount) }}</span>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>按位置查看</h3>
        <div class="chips" style="margin-bottom: 12px">
          <span
            v-for="loc in locations"
            :key="loc"
            class="chip"
            :class="{ active: selectedLocation === loc }"
            @click="selectLocation(loc)"
          >
            {{ loc }} ({{ data.location_counts[loc] }})
          </span>
        </div>

        <template v-if="selectedLocation">
          <div class="section-title">「{{ selectedLocation }}」分类占比</div>
          <PieChart v-if="locLabels.length" :labels="locLabels" :values="locValues" />

          <div class="section-title">「{{ selectedLocation }}」全部物品（{{ locationItems.length }}）</div>
          <div class="grid">
            <div v-for="item in locationItems" :key="item.id" class="card">
              <router-link :to="`/item/${item.id}/edit`">
                <img v-if="item.image" class="thumb" :src="`/uploads/${item.image}`" :alt="item.name" />
                <div v-else class="thumb-placeholder">📦</div>
              </router-link>
              <div class="body">
                <div class="title">{{ item.name }}</div>
                <div class="meta">
                  <span class="tag" v-if="item.category">{{ item.category }}</span>
                  <div>数量：{{ item.quantity }}</div>
                </div>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="empty">点击上方位置查看该位置的物品与分类占比</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.amount-table {
  margin-top: 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}
.amount-row {
  display: grid;
  grid-template-columns: 1fr 80px 120px;
  padding: 8px 12px;
  font-size: 14px;
  border-bottom: 1px solid var(--border);
}
.amount-row:last-child {
  border-bottom: none;
}
.amount-row span:nth-child(2),
.amount-row span:nth-child(3) {
  text-align: right;
}
.amount-head {
  background: var(--head-bg);
  font-weight: 600;
  color: var(--muted);
}
</style>
