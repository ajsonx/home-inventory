import { createRouter, createWebHistory } from 'vue-router'
import { api } from './api.js'

import Login from './views/Login.vue'
import ItemList from './views/ItemList.vue'
import ItemForm from './views/ItemForm.vue'
import BatchAdd from './views/BatchAdd.vue'
import Expiry from './views/Expiry.vue'
import Stats from './views/Stats.vue'
import Settings from './views/Settings.vue'
import Achievements from './views/Achievements.vue'

const routes = [
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  { path: '/', name: 'list', component: ItemList },
  { path: '/item/new', name: 'item-new', component: ItemForm },
  { path: '/item/:id/edit', name: 'item-edit', component: ItemForm, props: true },
  { path: '/batch', name: 'batch', component: BatchAdd },
  { path: '/expiry', name: 'expiry', component: Expiry },
  { path: '/achievements', name: 'achievements', component: Achievements },
  { path: '/stats', name: 'stats', component: Stats },
  { path: '/settings', name: 'settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局守卫：未登录访问受保护页面则跳转登录
let authChecked = false
let authed = false

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  if (!authChecked) {
    try {
      const res = await api.me()
      authed = !!res.authed
    } catch {
      authed = false
    }
    authChecked = true
  }
  if (!authed) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

// 登录成功后调用，刷新鉴权缓存
export function markAuthed(value) {
  authed = value
  authChecked = true
}

export default router
