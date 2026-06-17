<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'

const router = useRouter()
const items = ref([])
const loading = ref(false)
const soonDays = ref(30)

const startOfToday = new Date()
startOfToday.setHours(0, 0, 0, 0)

// 计算到期日（Date 或 null）：优先"存入日期 + 月数"，兼容旧的固定日期字段
function expiryDate(item) {
  if (item.expiry_months && item.created_at) {
    const d = new Date(item.created_at * 1000)
    d.setHours(0, 0, 0, 0)
    d.setMonth(d.getMonth() + item.expiry_months)
    return d
  }
  if (item.expiry_date) {
    const d = new Date(item.expiry_date + 'T00:00:00')
    return isNaN(d.getTime()) ? null : d
  }
  return null
}

function fmt(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}

function daysDiff(d) {
  return Math.round((d - startOfToday) / 86400000)
}

const decorated = computed(() =>
  items.value
    .map((it) => ({ it, exp: expiryDate(it) }))
    .filter((x) => x.exp)
    .sort((a, b) => a.exp - b.exp),
)

const expired = computed(() => decorated.value.filter((x) => daysDiff(x.exp) < 0))
const soon = computed(() =>
  decorated.value.filter((x) => {
    const dd = daysDiff(x.exp)
    return dd >= 0 && dd <= soonDays.value
  }),
)

const pendingDelete = ref(null)

async function load() {
  loading.value = true
  try {
    items.value = await api.listItems({})
  } catch (e) {
    if (e.code === 401) router.push({ name: 'login' })
  } finally {
    loading.value = false
  }
}

function confirmDelete(x) {
  pendingDelete.value = x
}

async function doDelete() {
  const x = pendingDelete.value
  if (!x) return
  try {
    await api.deleteItem(x.it.id)
    items.value = items.value.filter((i) => i.id !== x.it.id)
  } finally {
    pendingDelete.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="container">
    <p style="color: var(--muted); font-size: 13px; margin: 0 0 12px">
      删除过期/临期物品会计入「清垢除旧」清理成就（需已选择家庭成员身份）。
    </p>
    <div class="toolbar">
      <span style="align-self: center; color: var(--muted); font-size: 14px">临期范围（天）</span>
      <select v-model.number="soonDays" class="select" style="max-width: 120px">
        <option :value="7">7 天内</option>
        <option :value="15">15 天内</option>
        <option :value="30">30 天内</option>
        <option :value="60">60 天内</option>
        <option :value="90">90 天内</option>
      </select>
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <template v-else>
      <div class="section-title" style="color: var(--danger)">
        已过期（{{ expired.length }}）
      </div>
      <div v-if="expired.length === 0" class="empty">没有已过期的物品</div>
      <div v-else class="grid">
        <div v-for="x in expired" :key="x.it.id" class="card">
          <router-link :to="`/item/${x.it.id}/edit`">
            <img v-if="x.it.image" class="thumb" :src="`/uploads/${x.it.image}`" :alt="x.it.name" />
            <div v-else class="thumb-placeholder">📦</div>
          </router-link>
          <div class="body">
            <div class="title">{{ x.it.name }}</div>
            <div class="meta">
              <span class="tag" v-if="x.it.category">{{ x.it.category }}</span>
              <span class="tag" v-if="x.it.location">{{ x.it.location }}</span>
              <div>有效期至：{{ fmt(x.exp) }}</div>
              <div style="color: var(--danger)">已过期 {{ -daysDiff(x.exp) }} 天</div>
            </div>
            <div style="display:flex;gap:6px;margin-top:8px">
              <router-link class="btn" style="flex:1;padding:6px" :to="`/item/${x.it.id}/edit`">编辑</router-link>
              <button class="btn btn-danger" style="padding:6px" @click="confirmDelete(x)">清理</button>
            </div>
          </div>
        </div>
      </div>

      <div class="section-title" style="margin-top: 20px">
        即将到期（{{ soonDays }} 天内，{{ soon.length }}）
      </div>
      <div v-if="soon.length === 0" class="empty">近期没有要到期的物品</div>
      <div v-else class="grid">
        <div v-for="x in soon" :key="x.it.id" class="card">
          <router-link :to="`/item/${x.it.id}/edit`">
            <img v-if="x.it.image" class="thumb" :src="`/uploads/${x.it.image}`" :alt="x.it.name" />
            <div v-else class="thumb-placeholder">📦</div>
          </router-link>
          <div class="body">
            <div class="title">{{ x.it.name }}</div>
            <div class="meta">
              <span class="tag" v-if="x.it.category">{{ x.it.category }}</span>
              <span class="tag" v-if="x.it.location">{{ x.it.location }}</span>
              <div>有效期至：{{ fmt(x.exp) }}</div>
              <div style="color: #d97706">还剩 {{ daysDiff(x.exp) }} 天</div>
            </div>
            <div style="display:flex;gap:6px;margin-top:8px">
              <router-link class="btn" style="flex:1;padding:6px" :to="`/item/${x.it.id}/edit`">编辑</router-link>
              <button class="btn btn-danger" style="padding:6px" @click="confirmDelete(x)">清理</button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="pendingDelete" class="modal-mask" @click.self="pendingDelete = null">
      <div class="modal">
        <h3>确认清理</h3>
        <p>删除「{{ pendingDelete.it.name }}」？将计入清理成就。</p>
        <div class="actions">
          <button class="btn" @click="pendingDelete = null">取消</button>
          <button class="btn btn-danger" @click="doDelete">确认清理</button>
        </div>
      </div>
    </div>
  </div>
</template>
