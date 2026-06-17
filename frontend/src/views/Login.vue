<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import { markAuthed } from '../router.js'
import { member } from '../member.js'

const MEMBER_KEY = 'home_analy_member'

const mode = ref('login') // setup | login | register
const needsSetup = ref(false)
const registeredUsers = ref([])
const suggestions = ref(['女主人', '男主人'])

const selectedMember = ref(localStorage.getItem(MEMBER_KEY) || '')
const customMember = ref('')
const password = ref('')
const password2 = ref('')
const error = ref('')
const loading = ref(false)

const route = useRoute()
const router = useRouter()

const useCustom = computed(() => mode.value !== 'login' && !selectedMember.value)

const activeMember = computed(() => {
  if (mode.value === 'login') return selectedMember.value
  return selectedMember.value || customMember.value.trim()
})

async function loadStatus() {
  const st = await api.authStatus()
  needsSetup.value = st.needs_setup
  registeredUsers.value = st.users || []
  suggestions.value = st.suggestions?.length
    ? st.suggestions
    : ['女主人', '男主人']
  if (st.needs_setup) {
    mode.value = 'setup'
    selectedMember.value = suggestions.value[0] || '女主人'
  } else if (!selectedMember.value && st.users?.length) {
    selectedMember.value = st.users[0]
  }
}

async function submit() {
  if (loading.value) return
  error.value = ''
  const m = activeMember.value
  if (!m) {
    error.value = '请选择或填写身份'
    return
  }
  if (mode.value !== 'login') {
    if (password.value.length < 4) {
      error.value = '密码至少 4 位'
      return
    }
    if (password.value !== password2.value) {
      error.value = '两次密码不一致'
      return
    }
  }
  loading.value = true
  try {
    if (mode.value === 'setup') {
      const res = await api.setup(m, password.value)
      member.value = res.member
    } else if (mode.value === 'register') {
      await api.register(m, password.value)
      selectedMember.value = m
      customMember.value = ''
      mode.value = 'login'
      password.value = ''
      password2.value = ''
      await loadStatus()
      error.value = ''
      alert(`「${m}」注册成功，请用新密码登录`)
      return
    } else {
      const res = await api.login(m, password.value)
      member.value = res.member
    }
    localStorage.setItem(MEMBER_KEY, member.value)
    markAuthed(true)
    router.push(route.query.redirect || '/')
  } catch (e) {
    error.value = e.message || '操作失败'
  } finally {
    loading.value = false
  }
}

function switchMode(m) {
  mode.value = m
  error.value = ''
  password.value = ''
  password2.value = ''
}

onMounted(async () => {
  try {
    await loadStatus()
  } catch {
    error.value = '无法连接服务'
  }
})
</script>

<template>
  <div class="login-wrap">
    <form class="login-box" @submit.prevent="submit">
      <h1>家庭物品管理</h1>
      <p class="subtitle">
        <template v-if="mode === 'setup'">首次使用，请选择你的身份并设置密码</template>
        <template v-else-if="mode === 'register'">注册新的家庭成员账号</template>
        <template v-else>选择身份，输入你的专属密码登录</template>
      </p>

      <!-- 登录：已注册成员 -->
      <div v-if="mode === 'login'" class="field">
        <label>身份</label>
        <div class="chips" style="justify-content: center">
          <span
            v-for="u in registeredUsers"
            :key="u"
            class="chip"
            :class="{ active: selectedMember === u }"
            @click="selectedMember = u"
          >
            {{ u }}
          </span>
        </div>
      </div>

      <!-- 设置 / 注册：建议身份 + 自定义 -->
      <div v-else class="field">
        <label>选择身份</label>
        <div class="chips" style="justify-content: center">
          <span
            v-for="s in suggestions"
            :key="s"
            class="chip"
            :class="{ active: selectedMember === s && !customMember }"
            @click="selectedMember = s; customMember = ''"
          >
            {{ s }}
          </span>
          <span
            class="chip"
            :class="{ active: !!customMember || (selectedMember === '' && suggestions.length === 0) }"
            @click="selectedMember = ''"
          >
            自定义
          </span>
        </div>
        <input
          v-if="useCustom || suggestions.length === 0"
          v-model="customMember"
          class="input"
          style="margin-top: 8px"
          placeholder="输入身份名称，如 孩子 / 保姆"
        />
      </div>

      <div class="field">
        <input
          v-model="password"
          class="input"
          type="password"
          :placeholder="mode === 'login' ? '你的密码' : '设置密码（至少 4 位）'"
        />
      </div>
      <div v-if="mode !== 'login'" class="field">
        <input
          v-model="password2"
          class="input"
          type="password"
          placeholder="确认密码"
        />
      </div>

      <button class="btn btn-primary btn-block" type="submit" :disabled="loading">
        {{
          loading
            ? '请稍候...'
            : mode === 'setup'
              ? '完成设置并进入'
              : mode === 'register'
                ? '注册'
                : '登录'
        }}
      </button>
      <div class="error-text">{{ error }}</div>

      <div v-if="!needsSetup" class="mode-links">
        <template v-if="mode === 'login'">
          <a href="#" @click.prevent="switchMode('register')">注册新成员</a>
        </template>
        <template v-else-if="mode === 'register'">
          <a href="#" @click.prevent="switchMode('login')">返回登录</a>
        </template>
      </div>
    </form>
  </div>
</template>

<style scoped>
.subtitle {
  font-size: 13px;
  color: var(--muted);
  margin: 0 0 20px;
  line-height: 1.5;
}
.mode-links {
  margin-top: 16px;
  font-size: 14px;
}
.mode-links a {
  color: var(--primary);
}
</style>
