<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'
import { member } from '../member.js'

const router = useRouter()
const oldPwd = ref('')
const newPwd = ref('')
const newPwd2 = ref('')
const pwdMsg = ref('')
const pwdErr = ref('')
const pwdSaving = ref(false)
const tree = reactive({ categories: [], locations: [] })
const owners = reactive({ list: [] })
const newOwner = ref('')
const newParent = reactive({ categories: '', locations: '' })
const newChild = reactive({}) // key: `${kind}:${index}` -> string
const saving = ref(false)
const saved = ref(false)
const error = ref('')

function childKey(kind, idx) {
  return `${kind}:${idx}`
}

async function load() {
  try {
    const meta = await api.getMeta()
    tree.categories = meta.categories.map((c) => ({ name: c.name, children: [...c.children] }))
    tree.locations = meta.locations.map((l) => ({ name: l.name, children: [...l.children] }))
    owners.list = [...(meta.owners || [])]
  } catch (e) {
    if (e.code === 401) router.push({ name: 'login' })
  }
}

function addParent(kind) {
  const name = (newParent[kind] || '').trim()
  if (!name) return
  if (tree[kind].some((x) => x.name === name)) {
    error.value = `「${name}」已存在`
    return
  }
  tree[kind].push({ name, children: [] })
  newParent[kind] = ''
  error.value = ''
}

function removeParent(kind, idx) {
  tree[kind].splice(idx, 1)
}

function addChild(kind, idx) {
  const key = childKey(kind, idx)
  const name = (newChild[key] || '').trim()
  if (!name) return
  if (tree[kind][idx].children.includes(name)) {
    error.value = `「${name}」已存在`
    return
  }
  tree[kind][idx].children.push(name)
  newChild[key] = ''
  error.value = ''
}

function removeChild(kind, idx, cidx) {
  tree[kind][idx].children.splice(cidx, 1)
}

function addOwner() {
  const name = (newOwner.value || '').trim()
  if (!name) return
  if (owners.list.includes(name)) {
    error.value = `「${name}」已存在`
    return
  }
  owners.list.push(name)
  newOwner.value = ''
  error.value = ''
}

function removeOwner(idx) {
  owners.list.splice(idx, 1)
}

async function changePassword() {
  pwdErr.value = ''
  pwdMsg.value = ''
  if (newPwd.value.length < 4) {
    pwdErr.value = '新密码至少 4 位'
    return
  }
  if (newPwd.value !== newPwd2.value) {
    pwdErr.value = '两次新密码不一致'
    return
  }
  pwdSaving.value = true
  try {
    await api.changePassword(oldPwd.value, newPwd.value)
    pwdMsg.value = '密码已更新'
    oldPwd.value = ''
    newPwd.value = ''
    newPwd2.value = ''
  } catch (e) {
    pwdErr.value = e.message || '修改失败'
  } finally {
    pwdSaving.value = false
  }
}

async function save() {
  if (saving.value) return
  saving.value = true
  saved.value = false
  error.value = ''
  try {
    await api.updateMeta({
      categories: tree.categories,
      locations: tree.locations,
      owners: owners.list,
    })
    saved.value = true
    setTimeout(() => (saved.value = false), 2000)
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="container" style="max-width: 720px">
    <h2>设置</h2>

    <div class="chart-card">
      <h3>修改密码（{{ member }}）</h3>
      <p style="color: var(--muted); font-size: 13px; margin: 0 0 12px">
        每人独立密码，修改后请用新密码重新登录其它设备。
      </p>
      <div class="field">
        <input v-model="oldPwd" class="input" type="password" placeholder="当前密码" />
      </div>
      <div class="field">
        <input v-model="newPwd" class="input" type="password" placeholder="新密码（至少 4 位）" />
      </div>
      <div class="field">
        <input v-model="newPwd2" class="input" type="password" placeholder="确认新密码" />
      </div>
      <button class="btn btn-primary" :disabled="pwdSaving" @click="changePassword">
        {{ pwdSaving ? '保存中...' : '更新密码' }}
      </button>
      <div class="error-text">{{ pwdErr }}</div>
      <div v-if="pwdMsg" style="color: var(--primary); font-size: 13px; margin-top: 8px">{{ pwdMsg }}</div>
    </div>

    <p style="color: var(--muted); font-size: 13px">
      分类与位置支持两级；修改后点底部保存。
    </p>

    <div v-for="kind in ['categories', 'locations']" :key="kind" class="chart-card">
      <h3>{{ kind === 'categories' ? '物品分类' : '存放位置' }}</h3>

      <div v-for="(node, idx) in tree[kind]" :key="idx" class="node">
        <div class="node-head">
          <span class="node-name">{{ node.name }}</span>
          <button class="step-btn danger" @click="removeParent(kind, idx)">删除</button>
        </div>
        <div class="children">
          <span v-for="(c, cidx) in node.children" :key="cidx" class="chip">
            {{ c }}
            <span class="rm" @click="removeChild(kind, idx, cidx)">×</span>
          </span>
          <div class="child-add">
            <input
              v-model="newChild[childKey(kind, idx)]"
              class="input mini"
              :placeholder="kind === 'categories' ? '添加子分类' : '添加具体位置'"
              @keyup.enter="addChild(kind, idx)"
            />
            <button class="btn mini" @click="addChild(kind, idx)">+ 子级</button>
          </div>
        </div>
      </div>

      <div class="parent-add">
        <input
          v-model="newParent[kind]"
          class="input"
          :placeholder="kind === 'categories' ? '新增一级分类' : '新增一级位置'"
          @keyup.enter="addParent(kind)"
        />
        <button class="btn btn-primary" @click="addParent(kind)">+ 添加</button>
      </div>
    </div>

    <div class="chart-card">
      <h3>归属人</h3>
      <div class="chips">
        <span v-for="(o, idx) in owners.list" :key="idx" class="chip">
          {{ o }}
          <span class="rm" @click="removeOwner(idx)">×</span>
        </span>
      </div>
      <div class="parent-add">
        <input
          v-model="newOwner"
          class="input"
          placeholder="新增归属人（如 女主人 / 男主人 / 孩子）"
          @keyup.enter="addOwner"
        />
        <button class="btn btn-primary" @click="addOwner">+ 添加</button>
      </div>
    </div>

    <div class="error-text">{{ error }}</div>

    <div style="position: sticky; bottom: 0; padding: 12px 0; background: var(--bg)">
      <button class="btn btn-primary btn-block" :disabled="saving" @click="save">
        {{ saving ? '保存中...' : saved ? '已保存 ✓' : '保存全部修改' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.node {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 10px;
}
.node-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.node-name {
  font-weight: 600;
}
.children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.chip .rm {
  margin-left: 6px;
  color: var(--danger);
  cursor: pointer;
  font-weight: 700;
}
.child-add {
  display: flex;
  gap: 6px;
}
.input.mini {
  width: 140px;
  padding: 6px 10px;
  font-size: 13px;
}
.btn.mini {
  padding: 6px 10px;
  font-size: 13px;
}
.step-btn.danger {
  width: auto;
  padding: 4px 10px;
  height: auto;
  font-size: 13px;
  color: var(--danger);
  border-color: var(--border);
}
.parent-add {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
