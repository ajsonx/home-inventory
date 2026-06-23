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
    <div class="nav-menu">
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
    </div>
    <div class="nav-actions">
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
    </div>
  </nav>
  <router-view />
</template>

<style scoped>
.nav-menu,
.nav-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-actions {
  margin-left: auto;
}
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
  .navbar {
    flex-wrap: wrap;
    gap: 8px;
    padding: 8px 10px 10px;
  }
  .navbar .brand {
    flex: 1;
    font-size: 17px;
  }
  .nav-menu {
    order: 3;
    width: 100%;
    overflow-x: auto;
    padding: 4px 0 2px;
    scrollbar-width: none;
  }
  .nav-menu::-webkit-scrollbar {
    display: none;
  }
  .nav-link {
    flex: 0 0 auto;
    padding: 8px 12px;
    border: 1px solid var(--border);
    background: var(--input-bg);
    font-size: 14px;
  }
  .nav-link.active {
    border-color: var(--primary);
    box-shadow: 0 0 0 1px var(--primary);
  }
  .nav-actions {
    margin-left: 0;
    gap: 6px;
  }
  .nav-actions .btn {
    padding: 8px 10px;
    font-size: 13px;
  }
  .theme-toggle {
    width: 34px;
    height: 34px;
    font-size: 16px;
  }
  .member-badge {
    display: none;
  }
}
</style>
