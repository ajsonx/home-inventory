import { ref } from 'vue'
import { api } from './api.js'

const KEY = 'home_analy_member'
export const member = ref(localStorage.getItem(KEY) || '')

export async function syncMember() {
  try {
    const res = await api.me()
    if (res.member) {
      member.value = res.member
      localStorage.setItem(KEY, res.member)
    }
  } catch {
    /* ignore */
  }
}
