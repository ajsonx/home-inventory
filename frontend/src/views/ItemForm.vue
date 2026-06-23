<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.name === 'item-edit')
const itemId = computed(() => route.params.id)

const DRAFT_KEY = 'home_analy_item_draft'

const meta = ref({ locations: [], categories: [], owners: [] })
const form = ref({
  name: '',
  quantity: 1,
  category: '',
  subcategory: '',
  location: '',
  sublocation: '',
  owner: '',
  purchase_price: '',
  expiry_months: 0,
  created_date: '',
})

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

function tsToDateStr(ts) {
  if (!ts) return todayStr()
  const d = new Date(ts * 1000)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}
const imageFile = ref(null)
const previewUrl = ref('')
const existingImage = ref('')
const error = ref('')
const aiMessage = ref('')
const saving = ref(false)
const recognizing = ref(false)

// 内联添加的开关与输入文本
const adding = reactive({ cat: false, sub: false, loc: false, subloc: false, owner: false })
const addText = reactive({ cat: '', sub: '', loc: '', subloc: '', owner: '' })

const subCategories = computed(() => {
  const c = meta.value.categories.find((x) => x.name === form.value.category)
  return c ? c.children : []
})
const subLocations = computed(() => {
  const l = meta.value.locations.find((x) => x.name === form.value.location)
  return l ? l.children : []
})

function selectCategory(name) {
  if (form.value.category !== name) {
    form.value.category = name
    form.value.subcategory = ''
  }
}
function selectLocation(name) {
  if (form.value.location !== name) {
    form.value.location = name
    form.value.sublocation = ''
  }
}

// ---- 实时新增一级 / 二级（写入 meta 并即时选中） ----
async function addCategory() {
  const name = addText.cat.trim()
  if (!name) return
  if (!meta.value.categories.some((c) => c.name === name)) {
    meta.value.categories.push({ name, children: [] })
    meta.value = await api.updateMeta({ categories: meta.value.categories })
  }
  selectCategory(name)
  adding.cat = false
  addText.cat = ''
}
async function addSubcategory() {
  const name = addText.sub.trim()
  if (!name || !form.value.category) return
  const node = meta.value.categories.find((c) => c.name === form.value.category)
  if (!node) return
  if (!node.children.includes(name)) {
    node.children.push(name)
    meta.value = await api.updateMeta({ categories: meta.value.categories })
  }
  form.value.subcategory = name
  adding.sub = false
  addText.sub = ''
}
async function addLocation() {
  const name = addText.loc.trim()
  if (!name) return
  if (!meta.value.locations.some((l) => l.name === name)) {
    meta.value.locations.push({ name, children: [] })
    meta.value = await api.updateMeta({ locations: meta.value.locations })
  }
  selectLocation(name)
  adding.loc = false
  addText.loc = ''
}
async function addSublocation() {
  const name = addText.subloc.trim()
  if (!name || !form.value.location) return
  const node = meta.value.locations.find((l) => l.name === form.value.location)
  if (!node) return
  if (!node.children.includes(name)) {
    node.children.push(name)
    meta.value = await api.updateMeta({ locations: meta.value.locations })
  }
  form.value.sublocation = name
  adding.subloc = false
  addText.subloc = ''
}

async function addOwner() {
  const name = addText.owner.trim()
  if (!name) return
  if (!meta.value.owners.includes(name)) {
    meta.value.owners.push(name)
    meta.value = await api.updateMeta({ owners: meta.value.owners })
  }
  form.value.owner = name
  adding.owner = false
  addText.owner = ''
}

async function onFileChange(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  imageFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  if (!isEdit.value) await recognizeImage(file)
}

async function recognizeImage(file) {
  if (recognizing.value) return
  recognizing.value = true
  aiMessage.value = 'AI 正在识别图片...'
  try {
    const fd = new FormData()
    fd.append('image', file)
    const res = await api.recognizeItems(fd)
    const item = (res.items && res.items[0]) || null
    if (!item) {
      aiMessage.value = 'AI 未识别到明确物品，可手动填写'
      return
    }
    applyAiItem(item, res.shared || {})
    aiMessage.value = '已根据图片填充表单，可手动调整'
  } catch (e) {
    aiMessage.value = e.message || 'AI 识别失败，可手动填写'
  } finally {
    recognizing.value = false
  }
}

function applyAiItem(item, shared) {
  const next = { ...form.value }
  const textFields = ['name', 'category', 'subcategory', 'location', 'sublocation', 'owner']
  textFields.forEach((key) => {
    const value = item[key] || shared[key]
    if (value) next[key] = value
  })
  if (item.quantity) next.quantity = item.quantity
  if (item.purchase_price !== '' && item.purchase_price != null) {
    next.purchase_price = item.purchase_price
  }
  next.expiry_months = item.expiry_months || shared.expiry_months || next.expiry_months || 0
  form.value = next
}

async function loadMeta() {
  try {
    meta.value = await api.getMeta()
  } catch {
    /* ignore */
  }
}

async function loadItem() {
  if (!isEdit.value) return
  try {
    const item = await api.getItem(itemId.value)
    form.value = {
      name: item.name,
      quantity: item.quantity,
      category: item.category || '',
      subcategory: item.subcategory || '',
      location: item.location || '',
      sublocation: item.sublocation || '',
      owner: item.owner || '',
      purchase_price: item.purchase_price ?? '',
      expiry_months: item.expiry_months || 0,
      created_date: tsToDateStr(item.created_at),
    }
    existingImage.value = item.image || ''
  } catch (e) {
    if (e.code === 401) router.push({ name: 'login' })
  }
}

// ---- 草稿：仅新增模式，防止切走丢数据（图片需重选） ----
function restoreDraft() {
  const raw = localStorage.getItem(DRAFT_KEY)
  if (!raw) return
  try {
    Object.assign(form.value, JSON.parse(raw))
  } catch {
    /* ignore */
  }
}
function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
}
watch(
  form,
  (v) => {
    if (!isEdit.value) localStorage.setItem(DRAFT_KEY, JSON.stringify(v))
  },
  { deep: true },
)

async function submit() {
  if (saving.value) return
  error.value = ''
  if (!form.value.name.trim()) {
    error.value = '名称必填'
    return
  }
  saving.value = true
  const fd = new FormData()
  fd.append('name', form.value.name)
  fd.append('quantity', form.value.quantity || 1)
  fd.append('category', form.value.category)
  fd.append('subcategory', form.value.subcategory)
  fd.append('location', form.value.location)
  fd.append('sublocation', form.value.sublocation)
  fd.append('owner', form.value.owner)
  fd.append('purchase_price', form.value.purchase_price)
  fd.append('expiry_months', form.value.expiry_months || 0)
  fd.append('created_date', form.value.created_date || '')
  if (imageFile.value) fd.append('image', imageFile.value)
  try {
    if (isEdit.value) {
      await api.updateItem(itemId.value, fd)
    } else {
      await api.createItem(fd)
      clearDraft()
    }
    router.push('/')
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

function cancel() {
  if (!isEdit.value) clearDraft()
  router.push('/')
}

onMounted(() => {
  loadMeta()
  if (isEdit.value) {
    loadItem()
  } else {
    restoreDraft()
    if (!form.value.created_date) form.value.created_date = todayStr()
  }
})
</script>

<template>
  <div class="container item-form">
    <h2>{{ isEdit ? '编辑物品' : '新增物品' }}</h2>

    <div class="field">
      <label>照片</label>
      <img
        v-if="previewUrl"
        :src="previewUrl"
        class="photo-preview"
      />
      <img
        v-else-if="existingImage"
        :src="`/uploads/${existingImage}`"
        class="photo-preview"
      />
      <div class="photo-picker">
        <input id="item-photo" class="photo-input" type="file" accept="image/*" @change="onFileChange" />
        <label class="btn btn-primary photo-btn" for="item-photo">选择照片 / 拍照</label>
        <span class="photo-hint">{{ imageFile ? imageFile.name : '支持从相册选择，也可直接拍照' }}</span>
      </div>
      <div v-if="aiMessage" class="ai-hint" :class="{ loading: recognizing }">{{ aiMessage }}</div>
    </div>

    <div class="field">
      <label>名称 *</label>
      <input v-model="form.name" class="input" placeholder="物品名称" />
    </div>

    <div class="field">
      <label>数量</label>
      <input v-model.number="form.quantity" class="input" type="number" min="1" />
    </div>

    <div class="field">
      <label>分类</label>
      <div class="chips">
        <span
          v-for="c in meta.categories"
          :key="c.name"
          class="chip"
          :class="{ active: form.category === c.name }"
          @click="selectCategory(c.name)"
        >
          {{ c.name }}
        </span>
        <span v-if="!adding.cat" class="chip add" @click="adding.cat = true">＋</span>
        <span v-else class="inline-add">
          <input
            v-model="addText.cat"
            class="input mini"
            placeholder="新一级分类"
            @keyup.enter="addCategory"
          />
          <button class="btn mini btn-primary" @click="addCategory">加</button>
          <button class="btn mini" @click="adding.cat = false">×</button>
        </span>
      </div>

      <div v-if="form.category" class="chips" style="margin-top: 8px">
        <span class="sub-label">子分类:</span>
        <span
          class="chip"
          :class="{ active: form.subcategory === '' }"
          @click="form.subcategory = ''"
        >
          无
        </span>
        <span
          v-for="sc in subCategories"
          :key="sc"
          class="chip"
          :class="{ active: form.subcategory === sc }"
          @click="form.subcategory = sc"
        >
          {{ sc }}
        </span>
        <span v-if="!adding.sub" class="chip add" @click="adding.sub = true">＋</span>
        <span v-else class="inline-add">
          <input
            v-model="addText.sub"
            class="input mini"
            placeholder="新子分类"
            @keyup.enter="addSubcategory"
          />
          <button class="btn mini btn-primary" @click="addSubcategory">加</button>
          <button class="btn mini" @click="adding.sub = false">×</button>
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
          :class="{ active: form.location === loc.name }"
          @click="selectLocation(loc.name)"
        >
          {{ loc.name }}
        </span>
        <span v-if="!adding.loc" class="chip add" @click="adding.loc = true">＋</span>
        <span v-else class="inline-add">
          <input
            v-model="addText.loc"
            class="input mini"
            placeholder="新一级位置"
            @keyup.enter="addLocation"
          />
          <button class="btn mini btn-primary" @click="addLocation">加</button>
          <button class="btn mini" @click="adding.loc = false">×</button>
        </span>
      </div>

      <div v-if="form.location" class="chips" style="margin-top: 8px">
        <span class="sub-label">具体位置:</span>
        <span
          class="chip"
          :class="{ active: form.sublocation === '' }"
          @click="form.sublocation = ''"
        >
          无
        </span>
        <span
          v-for="sl in subLocations"
          :key="sl"
          class="chip"
          :class="{ active: form.sublocation === sl }"
          @click="form.sublocation = sl"
        >
          {{ sl }}
        </span>
        <span v-if="!adding.subloc" class="chip add" @click="adding.subloc = true">＋</span>
        <span v-else class="inline-add">
          <input
            v-model="addText.subloc"
            class="input mini"
            placeholder="新具体位置"
            @keyup.enter="addSublocation"
          />
          <button class="btn mini btn-primary" @click="addSublocation">加</button>
          <button class="btn mini" @click="adding.subloc = false">×</button>
        </span>
      </div>
    </div>

    <div class="field">
      <label>归属人</label>
      <div class="chips">
        <span
          v-for="o in meta.owners"
          :key="o"
          class="chip"
          :class="{ active: form.owner === o }"
          @click="form.owner = o"
        >
          {{ o }}
        </span>
        <span v-if="!adding.owner" class="chip add" @click="adding.owner = true">＋</span>
        <span v-else class="inline-add">
          <input
            v-model="addText.owner"
            class="input mini"
            placeholder="新归属人"
            @keyup.enter="addOwner"
          />
          <button class="btn mini btn-primary" @click="addOwner">加</button>
          <button class="btn mini" @click="adding.owner = false">×</button>
        </span>
      </div>
    </div>

    <div class="field">
      <label>购入价格（可选）</label>
      <input
        v-model="form.purchase_price"
        class="input"
        type="number"
        min="0"
        step="0.01"
        placeholder="例如 99.90"
      />
    </div>

    <div class="field">
      <label>有效期（从存入日期起算）</label>
      <div class="chips">
        <span
          v-for="opt in EXPIRY_OPTIONS"
          :key="opt.value"
          class="chip"
          :class="{ active: form.expiry_months === opt.value }"
          @click="form.expiry_months = opt.value"
        >
          {{ opt.label }}
        </span>
      </div>
    </div>

    <div class="field">
      <label>存入日期</label>
      <input v-model="form.created_date" class="input" type="date" />
    </div>

    <div class="error-text">{{ error }}</div>

    <div class="form-actions">
      <button class="btn" style="flex: 1" @click="cancel">取消</button>
      <button class="btn btn-primary" style="flex: 2" :disabled="saving" @click="submit">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.item-form {
  max-width: 560px;
}
.item-form .field {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.photo-preview {
  width: 100%;
  max-height: 280px;
  object-fit: contain;
  border-radius: 10px;
  background: var(--thumb-bg);
}
.photo-picker {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}
.photo-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.photo-btn {
  flex: 0 0 auto;
}
.photo-hint {
  min-width: 0;
  color: var(--muted);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ai-hint {
  margin-top: 8px;
  color: var(--muted);
  font-size: 13px;
}
.ai-hint.loading {
  color: var(--primary-dark);
}
.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}
.sub-label {
  align-self: center;
  font-size: 13px;
  color: var(--muted);
  margin-right: 2px;
}
.chip.add {
  border-style: dashed;
  color: var(--primary);
  font-weight: 700;
}
.inline-add {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.input.mini {
  width: 120px;
  padding: 6px 10px;
  font-size: 13px;
}
.btn.mini {
  padding: 6px 10px;
  font-size: 13px;
}
@media (max-width: 700px) {
  .item-form {
    padding: 14px;
  }
  .item-form h2 {
    margin-top: 4px;
  }
  .item-form .field {
    margin-bottom: 18px;
    padding-bottom: 18px;
  }
  .item-form .field label {
    margin-bottom: 10px;
    font-size: 15px;
  }
  .item-form .chips {
    gap: 10px;
  }
  .item-form .chip {
    padding: 9px 14px;
    font-size: 15px;
  }
  .sub-label {
    width: 100%;
    margin: 2px 0 0;
    font-size: 14px;
  }
  .inline-add {
    width: 100%;
    flex-wrap: wrap;
  }
  .input.mini {
    flex: 1 1 160px;
    width: auto;
    font-size: 14px;
  }
  .photo-picker {
    align-items: stretch;
    flex-direction: column;
  }
  .photo-btn {
    width: 100%;
  }
  .photo-hint {
    white-space: normal;
  }
}
</style>
