<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'

const router = useRouter()
const items = ref([])
const meta = ref({ locations: [], categories: [] })
const q = ref('')
const location = ref('')
const category = ref('')
const sortBy = ref('created_desc')
const loading = ref(false)

const pendingDelete = ref(null)
const nowSec = Math.floor(Date.now() / 1000)

function fmtDate(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}

// 到期日：优先用"存入日期 + 有效期月数"，兼容旧的固定日期字段
function expiryText(item) {
  if (item.expiry_months && item.created_at) {
    const d = new Date(item.created_at * 1000)
    d.setMonth(d.getMonth() + item.expiry_months)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
      d.getDate(),
    ).padStart(2, '0')}`
  }
  return item.expiry_date || ''
}

// 存入时长（天）
function storageDays(item) {
  if (!item.created_at) return 0
  return Math.floor((nowSec - item.created_at) / 86400)
}

// 使用成本 = 购入价格 / 使用次数
function useCost(item) {
  const price = item.purchase_price
  const count = item.use_count || 0
  if (price == null || price === '' || count <= 0) return null
  return price / count
}

function fmtMoney(v) {
  if (v == null || v === '') return '-'
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const sortedItems = computed(() => {
  const arr = [...items.value]
  switch (sortBy.value) {
    case 'use_asc':
      arr.sort((a, b) => (a.use_count || 0) - (b.use_count || 0))
      break
    case 'duration_desc':
      arr.sort((a, b) => (a.created_at || 0) - (b.created_at || 0))
      break
    case 'cost_desc':
      arr.sort((a, b) => (useCost(b) ?? -1) - (useCost(a) ?? -1))
      break
    case 'price_desc':
      arr.sort((a, b) => (b.purchase_price ?? -1) - (a.purchase_price ?? -1))
      break
    default:
      arr.sort((a, b) => (b.created_at || 0) - (a.created_at || 0))
  }
  return arr
})

async function load() {
  loading.value = true
  try {
    items.value = await api.listItems({
      q: q.value,
      location: location.value,
      category: category.value,
    })
  } catch (e) {
    if (e.code === 401) router.push({ name: 'login' })
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  try {
    meta.value = await api.getMeta()
  } catch {
    /* ignore */
  }
}

function toggleLocation(loc) {
  location.value = location.value === loc ? '' : loc
  load()
}

async function changeUse(item, delta) {
  try {
    const updated = await api.adjustUseCount(item.id, delta)
    item.use_count = updated.use_count
  } catch {
    /* ignore */
  }
}

function confirmDelete(item) {
  pendingDelete.value = item
}

async function doDelete() {
  const item = pendingDelete.value
  if (!item) return
  try {
    await api.deleteItem(item.id)
    items.value = items.value.filter((i) => i.id !== item.id)
  } finally {
    pendingDelete.value = null
  }
}

onMounted(() => {
  loadMeta()
  load()
})
</script>

<template>
  <div class="container">
    <div class="toolbar">
      <input
        v-model="q"
        class="input search"
        placeholder="搜索名称 / 分类 / 位置"
        @keyup.enter="load"
      />
      <select v-model="category" class="select" style="max-width: 120px" @change="load">
        <option value="">全部分类</option>
        <option v-for="c in meta.categories" :key="c.name" :value="c.name">{{ c.name }}</option>
      </select>
      <select v-model="sortBy" class="select" style="max-width: 140px">
        <option value="created_desc">最近存入</option>
        <option value="use_asc">使用次数少→多</option>
        <option value="duration_desc">存入时长久→近</option>
        <option value="cost_desc">使用成本高→低</option>
        <option value="price_desc">购入价格高→低</option>
      </select>
      <button class="btn btn-primary" @click="load">搜索</button>
    </div>

    <div class="chips" style="margin-bottom: 16px">
      <span class="chip" :class="{ active: location === '' }" @click="toggleLocation('')">
        全部位置
      </span>
      <span
        v-for="loc in meta.locations"
        :key="loc.name"
        class="chip"
        :class="{ active: location === loc.name }"
        @click="toggleLocation(loc.name)"
      >
        {{ loc.name }}
      </span>
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="items.length === 0" class="empty">暂无物品，点击右上角「+ 新增」添加</div>

    <div v-else class="grid">
      <div v-for="item in sortedItems" :key="item.id" class="card">
        <router-link :to="`/item/${item.id}/edit`">
          <img v-if="item.image" class="thumb" :src="`/uploads/${item.image}`" :alt="item.name" />
          <div v-else class="thumb-placeholder">📦</div>
        </router-link>
        <div class="body">
          <div class="title">{{ item.name }}</div>
          <div class="meta">
            <div style="margin-bottom: 4px">
              <span class="tag" v-if="item.category">
                {{ item.category }}<template v-if="item.subcategory"> / {{ item.subcategory }}</template>
              </span>
            </div>
            <div style="margin-bottom: 4px">
              <span class="tag" v-if="item.location">
                {{ item.location }}<template v-if="item.sublocation"> / {{ item.sublocation }}</template>
              </span>
            </div>
            <div v-if="item.owner" style="margin-bottom: 4px">
              <span class="tag owner-tag">{{ item.owner }}</span>
            </div>
            <div>数量：{{ item.quantity }}</div>
            <div v-if="item.purchase_price != null && item.purchase_price !== ''">
              购入价：{{ fmtMoney(item.purchase_price) }}
            </div>
            <div v-if="expiryText(item)">有效期至：{{ expiryText(item) }}</div>
            <div>存入：{{ fmtDate(item.created_at) }}（{{ storageDays(item) }} 天）</div>
            <div v-if="useCost(item) != null">使用成本：{{ fmtMoney(useCost(item)) }} / 次</div>
          </div>

          <div class="use-row">
            <span class="use-label">使用</span>
            <button class="step-btn" @click="changeUse(item, -1)">−</button>
            <span class="use-count">{{ item.use_count || 0 }}</span>
            <button class="step-btn" @click="changeUse(item, 1)">＋</button>
            <span class="use-unit">次</span>
          </div>

          <div style="display: flex; gap: 6px; margin-top: 8px">
            <router-link class="btn" style="flex: 1; padding: 6px" :to="`/item/${item.id}/edit`">
              编辑
            </router-link>
            <button class="btn btn-danger" style="padding: 6px" @click="confirmDelete(item)">
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="pendingDelete" class="modal-mask" @click.self="pendingDelete = null">
      <div class="modal">
        <h3>确认删除</h3>
        <p>确定要删除「{{ pendingDelete.name }}」吗？此操作不可恢复。</p>
        <div class="actions">
          <button class="btn" @click="pendingDelete = null">取消</button>
          <button class="btn btn-danger" @click="doDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.owner-tag {
  background: var(--thumb-bg);
  color: var(--text);
}
.use-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
}
.use-label,
.use-unit {
  font-size: 12px;
  color: var(--muted);
}
.use-count {
  min-width: 20px;
  text-align: center;
  font-weight: 600;
}
.step-btn {
  width: 26px;
  height: 26px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--input-bg);
  font-size: 16px;
  line-height: 1;
  color: var(--text);
}
.step-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}
</style>
