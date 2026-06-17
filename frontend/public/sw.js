// 家庭物品管理 PWA Service Worker
// 策略：
// - /api 与 /uploads：完全不拦截（始终走网络，保证数据与图片实时、登录态正确）
// - 导航请求(HTML)：网络优先，失败时回退缓存的 index.html（离线可打开壳）
// - 静态资源(js/css/图标等同源 GET)：缓存优先 + 后台更新(stale-while-revalidate)

const CACHE = 'home-analy-v1'
const APP_SHELL = '/index.html'

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll([APP_SHELL, '/'])).catch(() => {}),
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ),
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)

  // 跨域请求不处理
  if (url.origin !== self.location.origin) return

  // 动态接口与图片：直接放行，不缓存
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/uploads')) {
    return
  }

  // 导航请求：网络优先，离线回退到缓存壳
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((resp) => {
          const copy = resp.clone()
          caches.open(CACHE).then((c) => c.put(APP_SHELL, copy)).catch(() => {})
          return resp
        })
        .catch(() => caches.match(APP_SHELL)),
    )
    return
  }

  // 静态资源：stale-while-revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((resp) => {
          if (resp && resp.status === 200) {
            const copy = resp.clone()
            caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {})
          }
          return resp
        })
        .catch(() => cached)
      return cached || network
    }),
  )
})
