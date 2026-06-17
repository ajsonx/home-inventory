<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from './api.js'
import { markAuthed } from './router.js'
import { theme, toggleTheme } from './theme.js'
import { member, syncMember } from './member.js'

const route = useRoute()
const router = useRouter()

const showNav = computed(() => route.name !== 'login')

onMounted(syncMember)

async function logout() {
  try {
    await api.logout()
  } finally {
    markAuthed(false)
    member.value = ''
    router.push({ name: 'login' })
  }
}
</script>

<template>
  <nav v-if="showNav" class="navbar">
    <span class="brand">家庭物品</span>
    <router-link class="nav-link" :class="{ active: route.name === 'list' }" to="/">
      物品
    </router-link>
    <router-link class="nav-link" :class="{ active: route.name === 'batch' }" to="/batch">
      批量
    </router-link>
    <router-link class="nav-link" :class="{ active: route.name === 'expiry' }" to="/expiry">
      临期
    </router-link>
    <router-link class="nav-link" :class="{ active: route.name === 'achievements' }" to="/achievements">
      成就
    </router-link>
    <router-link class="nav-link" :class="{ active: route.name === 'stats' }" to="/stats">
      统计
    </router-link>
    <router-link class="nav-link" :class="{ active: route.name === 'settings' }" to="/settings">
      设置
    </router-link>
    <span class="spacer"></span>
    <span v-if="member" class="member-badge">{{ member }}</span>
    <button
      class="theme-toggle"
      :title="theme === 'dark' ? '切换到日间模式' : '切换到夜间模式'"
      @click="toggleTheme"
    >
      {{ theme === 'dark' ? '☀️' : '🌙' }}
    </button>
    <router-link class="btn btn-primary" to="/item/new">+ 新增</router-link>
    <button class="btn" @click="logout">退出</button>
  </nav>
  <router-view />
</template>

<style scoped>
.member-badge {
  font-size: 13px;
  color: var(--muted);
  padding: 4px 10px;
  border-radius: 8px;
  background: var(--accent-soft);
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 700px) {
  .nav-link {
    padding: 6px 8px;
    font-size: 13px;
  }
  .member-badge {
    display: none;
  }
}
</style>
