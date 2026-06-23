// 统一 API 封装。所有请求带 credentials 以携带 session cookie。

async function request(url, options = {}) {
  const opts = { credentials: 'include', ...options }
  const resp = await fetch(url, opts)
  if (resp.status === 401) {
    const err = new Error('unauthorized')
    err.code = 401
    throw err
  }
  const isJson = (resp.headers.get('content-type') || '').includes('application/json')
  const body = isJson ? await resp.json() : null
  if (!resp.ok) {
    const err = new Error((body && body.error) || `请求失败(${resp.status})`)
    err.code = resp.status
    throw err
  }
  return body
}

export const api = {
  // 鉴权
  authStatus: () => request('/api/auth/status'),
  setup: (member, password) =>
    request('/api/auth/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ member, password }),
    }),
  register: (member, password) =>
    request('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ member, password }),
    }),
  login: (member, password) =>
    request('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ member, password }),
    }),
  changePassword: (oldPassword, newPassword) =>
    request('/api/auth/change_password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    }),
  logout: () => request('/api/logout', { method: 'POST' }),
  me: () => request('/api/me'),

  // meta
  getMeta: () => request('/api/meta'),
  updateMeta: (payload) =>
    request('/api/meta', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // items
  listItems: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.q) qs.set('q', params.q)
    if (params.location) qs.set('location', params.location)
    if (params.category) qs.set('category', params.category)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request(`/api/items${suffix}`)
  },
  getItem: (id) => request(`/api/items/${id}`),
  createItem: (formData) =>
    request('/api/items', { method: 'POST', body: formData }),
  batchCreate: (formData) =>
    request('/api/items/batch', { method: 'POST', body: formData }),
  updateItem: (id, formData) =>
    request(`/api/items/${id}`, { method: 'PUT', body: formData }),
  deleteItem: (id) => request(`/api/items/${id}`, { method: 'DELETE' }),
  adjustUseCount: (id, delta) =>
    request(`/api/items/${id}/use_count`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta }),
    }),

  // ai
  recognizeItems: (formData) =>
    request('/api/ai/recognize_items', { method: 'POST', body: formData }),

  // stats
  stats: () => request('/api/stats'),

  // achievements
  achievements: () => request('/api/achievements'),
  claimAchievement: (id) =>
    request('/api/achievements/claim', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    }),
}
