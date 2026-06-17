import { ref } from 'vue'

const KEY = 'home_analy_theme'

function initialTheme() {
  const saved = localStorage.getItem(KEY)
  if (saved === 'dark' || saved === 'light') return saved
  // 默认跟随系统
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

export const theme = ref(initialTheme())

export function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t)
}

export function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem(KEY, theme.value)
  applyTheme(theme.value)
}

// 模块加载即应用一次，确保与初始值一致
applyTheme(theme.value)
