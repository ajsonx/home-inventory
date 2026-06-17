<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'

const router = useRouter()
const meta = ref({ locations: [], categories: [], owners: [] })

const EXPIRY_OPTIONS = [
  { label: '无', value: 0 },
  { label: '3个月', value: 3 },
  { label: '6个月', value: 6 },
  { label: '1年', value: 12 },
  { label: '2年', value: 24 },
]

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}

// 共享字段（这一批物品公用）
const shared = ref({
  category: '',
  subcategory: '',
  location: '',
  sublocation: '',
  owner: '',
  expiry_months: 0,
  created_date: todayStr(),
})

function newRow() {
  return { name: '', quantity: 1, purchase_price: '' }
}
const rows = ref([newRow(), newRow(), newRow()])

const imageFile = ref(null)
const previewUrl = ref('')
const saving = ref(false)
const error = ref('')
const result = ref('')

function onFileChange(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  imageFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

const subCategories = computed(() => {
  const c = meta.value.categories.find((x) => x.name === shared.value.category)
  return c ? c.children : []
})
const subLocations = computed(() => {
  const l = meta.value.locations.find((x) => x.name === shared.value.location)
  return l ? l.children : []
})

function selectCategory(name) {
  if (shared.value.category !== name) {
    shared.value.category = name
    shared.value.subcategory = ''
  }
}
function selectLocation(name) {
  if (shared.value.location !== name) {
    shared.value.location = name
    shared.value.sublocation = ''
  }
}

function addRow() {
  rows.value.push(newRow())
}
function removeRow(idx) {
  rows.value.splice(idx, 1)
  if (rows.value.length === 0) rows.value.push(newRow())
}
function onNameEnter(idx) {
  if (idx === rows.value.length - 1) addRow()
}

const validCount = computed(() => rows.value.filter((r) => r.name.trim()).length)

async function loadMeta() {
  try {
    meta.value = await api.getMeta()
  } catch (e) {
    if (e.code === 401) router.push({ name: 'login' })
  }
}

async function submit() {
  if (saving.value) return
  error.value = ''
  result.value = ''
  const items = rows.value
    .filter((r) => r.name.trim())
    .map((r) => ({
      name: r.name.trim(),
      quantity: r.quantity || 1,
      purchase_price: r.purchase_price,
    }))
  if (items.length === 0) {
    error.value = '请至少填写一行物品名称'
    return
  }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('payload', JSON.stringify({ shared: shared.value, items }))
    if (imageFile.value) fd.append('image', imageFile.value)
    const res = await api.batchCreate(fd)
    result.value = `成功添加 ${res.created} 件物品`
    rows.value = [newRow(), newRow(), newRow()]
    imageFile.value = null
    previewUrl.value = ''
  } catch (e) {
    error.value = e.message || '批量添加失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadMeta)
</script>

<template>
  <div class="container" style="max-width: 720px">
    <h2>批量添加</h2>
    <p style="color: var(--muted); font-size: 13px">
      下方"共享设置"对本批所有物品生效，逐行只需填名称（数量默认 1，价格可选）。图片可稍后在列表里单独补。
    </p>

    <div class="chart-card">
      <h3>共享设置</h3>

      <div class="field">
        <label>分类</label>
        <div class="chips">
          <span
            v-for="c in meta.categories"
            :key="c.name"
            class="chip"
            :class="{ active: shared.category === c.name }"
            @click="selectCategory(c.name)"
          >
            {{ c.name }}
          </span>
        </div>
        <div v-if="shared.category && subCategories.length" class="chips" style="margin-top: 8px">
          <span class="sub-label">子分类:</span>
          <span class="chip" :class="{ active: shared.subcategory === '' }" @click="shared.subcategory = ''">无</span>
          <span
            v-for="sc in subCategories"
            :key="sc"
            class="chip"
            :class="{ active: shared.subcategory === sc }"
            @click="shared.subcategory = sc"
          >
            {{ sc }}
          </span>
        </div>
      </div>

      <div class="field">
        <label>存放位置</label>
        <div class="chips">
          <span
            v-for="loc in meta.locations"
            :key="loc.name"
            class="chip"
            :class="{ active: shared.location === loc.name }"
            @click="selectLocation(loc.name)"
          >
            {{ loc.name }}
          </span>
        </div>
        <div v-if="shared.location && subLocations.length" class="chips" style="margin-top: 8px">
          <span class="sub-label">具体位置:</span>
          <span class="chip" :class="{ active: shared.sublocation === '' }" @click="shared.sublocation = ''">无</span>
          <span
            v-for="sl in subLocations"
            :key="sl"
            class="chip"
            :class="{ active: shared.sublocation === sl }"
            @click="shared.sublocation = sl"
          >
            {{ sl }}
          </span>
        </div>
      </div>

      <div class="field">
        <label>归属人</label>
        <div class="chips">
          <span class="chip" :class="{ active: shared.owner === '' }" @click="shared.owner = ''">无</span>
          <span
            v-for="o in meta.owners"
            :key="o"
            class="chip"
            :class="{ active: shared.owner === o }"
            @click="shared.owner = o"
          >
            {{ o }}
          </span>
        </div>
      </div>

      <div class="field">
        <label>有效期（从存入日期起算）</label>
        <div class="chips">
          <span
            v-for="opt in EXPIRY_OPTIONS"
            :key="opt.value"
            class="chip"
            :class="{ active: shared.expiry_months === opt.value }"
            @click="shared.expiry_months = opt.value"
          >
            {{ opt.label }}
          </span>
        </div>
      </div>

      <div class="field">
        <label>存入日期</label>
        <input v-model="shared.created_date" class="input" type="date" />
      </div>

      <div class="field">
        <label>共享图片（可选，本批所有物品共用，如柜子整体照）</label>
        <img
          v-if="previewUrl"
          :src="previewUrl"
          style="width: 100%; max-height: 240px; object-fit: contain; border-radius: 10px; background: var(--thumb-bg)"
        />
        <input
          type="file"
          accept="image/*"
          capture="environment"
          style="margin-top: 8px"
          @change="onFileChange"
        />
      </div>
    </div>

    <div class="chart-card">
      <h3>物品清单（{{ validCount }} 件）</h3>
      <div class="batch-row batch-head">
        <span>名称</span>
        <span>数量</span>
        <span>价格</span>
        <span></span>
      </div>
      <div v-for="(r, idx) in rows" :key="idx" class="batch-row">
        <input
          v-model="r.name"
          class="input"
          placeholder="物品名称"
          @keyup.enter="onNameEnter(idx)"
        />
        <input v-model.number="r.quantity" class="input" type="number" min="1" />
        <input v-model="r.purchase_price" class="input" type="number" min="0" step="0.01" placeholder="可选" />
        <button class="step-btn danger" @click="removeRow(idx)">×</button>
      </div>
      <button class="btn" style="margin-top: 10px" @click="addRow">+ 添加一行</button>
    </div>

    <div class="error-text">{{ error }}</div>
    <div v-if="result" style="color: var(--primary); font-size: 14px; margin-bottom: 8px">
      {{ result }}（<router-link to="/" style="color: var(--primary); text-decoration: underline">去列表查看</router-link>）
    </div>

    <div style="position: sticky; bottom: 0; padding: 12px 0; background: var(--bg)">
      <button class="btn btn-primary btn-block" :disabled="saving" @click="submit">
        {{ saving ? '提交中...' : `批量添加 ${validCount} 件` }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.batch-row {
  display: grid;
  grid-template-columns: 1fr 80px 100px 34px;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.batch-head {
  font-size: 13px;
  color: var(--muted);
  font-weight: 600;
  margin-bottom: 4px;
}
.sub-label {
  align-self: center;
  font-size: 13px;
  color: var(--muted);
  margin-right: 2px;
}
.step-btn.danger {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--danger);
  font-size: 16px;
}
</style>
