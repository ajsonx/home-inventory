<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'
import { member, syncMember } from '../member.js'
import AchievementArt from '../components/AchievementArt.vue'

const router = useRouter()
const data = ref(null)
const loading = ref(false)
const claiming = ref('')
const claimModal = ref(null)

function progressText(item) {
  const p = item.progress || {}
  if (p.unit === '%') return `${p.current}% / ${p.target}%`
  if (p.unit === '元') return `CNY ${Number(p.current).toLocaleString()} / ${p.target}`
  if (p.extra) return `${p.current} / ${p.target}（${p.extra}）`
  return `${p.current} / ${p.target}`
}

async function load() {
  loading.value = true
  try {
    await syncMember()
    data.value = await api.achievements()
  } catch (e) {
    if (e.code === 401) router.push({ name: 'login' })
  } finally {
    loading.value = false
  }
}

async function claim(item) {
  if (claiming.value || !item.eligible) return
  claiming.value = item.id
  try {
    const res = await api.claimAchievement(item.id)
    claimModal.value = res
    await load()
  } catch (e) {
    alert(e.message || '领取失败')
  } finally {
    claiming.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div class="container ach-page">
    <div v-if="!member" class="chart-card warn-box">
      <p>请登录后查看成就（成就按登录身份统计）。</p>
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <template v-else-if="data">
      <div class="ach-header">
        <h2>家庭成就</h2>
        <p v-if="member">
          当前成员：<strong>{{ member }}</strong>
          · 已领取维护基金合计
          <strong>CNY {{ Number(data.total_fund_claimed || 0).toLocaleString() }}</strong>
        </p>
      </div>

      <div class="stats-row" v-if="member && data.stats">
        <div class="stat-chip">录入 {{ data.stats.entry_count }}</div>
        <div class="stat-chip">带图 {{ data.stats.entry_with_image }}</div>
        <div class="stat-chip">规范分类 {{ data.stats.classify_count }}</div>
        <div class="stat-chip">清理 {{ data.stats.cleanup_count }}</div>
      </div>

      <div v-for="group in data.groups" :key="group.id" class="ach-group">
        <h3 class="group-title">{{ group.name }}</h3>
        <div class="ach-grid">
          <div
            v-for="item in group.items"
            :key="item.id"
            class="ach-card"
            :class="{ claimed: item.claimed, eligible: item.eligible }"
          >
            <div class="ach-card-top">
              <span class="ach-icon">{{ item.icon }}</span>
              <AchievementArt v-if="item.art" :art="item.art" />
            </div>
            <div class="ach-title">{{ item.title }}</div>
            <div class="ach-desc">{{ item.desc }}</div>
            <div class="ach-fund">维护基金 CNY {{ item.fund }}</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: item.percent + '%' }"></div>
            </div>
            <div class="progress-text">{{ progressText(item) }}</div>
            <button
              v-if="item.claimed"
              class="btn btn-block claimed-btn"
              disabled
            >
              已领取 ✓
            </button>
            <button
              v-else-if="item.eligible"
              class="btn btn-primary btn-block"
              :disabled="claiming === item.id"
              @click="claim(item)"
            >
              {{ claiming === item.id ? '领取中...' : '领取成就' }}
            </button>
            <button v-else class="btn btn-block" disabled>未达成</button>
          </div>
        </div>
      </div>
    </template>

    <!-- 领取成功弹窗 -->
    <div v-if="claimModal" class="modal-mask" @click.self="claimModal = null">
      <div class="modal ach-modal">
        <AchievementArt v-if="claimModal.art" :art="claimModal.art" />
        <div class="modal-icon">{{ claimModal.icon }}</div>
        <h3>【{{ claimModal.title }}】</h3>
        <p>{{ claimModal.popup }}</p>
        <button class="btn btn-primary btn-block" @click="claimModal = null">太好了</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ach-page {
  max-width: 900px;
}
.ach-header h2 {
  margin: 0 0 6px;
}
.ach-header p {
  color: var(--muted);
  font-size: 14px;
  margin: 0 0 16px;
}
.warn-box p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}
.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.stat-chip {
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--primary-dark);
  font-size: 13px;
}
.group-title {
  margin: 0 0 12px;
  font-size: 17px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.ach-group {
  margin-bottom: 28px;
}
.ach-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.ach-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}
.ach-card.eligible {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary);
}
.ach-card.claimed {
  opacity: 0.85;
  background: var(--accent-soft);
}
.ach-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  min-height: 56px;
}
.ach-icon {
  font-size: 32px;
}
.ach-title {
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 4px;
}
.ach-desc {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 8px;
  line-height: 1.5;
}
.ach-fund {
  font-size: 13px;
  color: var(--primary-dark);
  margin-bottom: 10px;
}
.progress-bar {
  height: 6px;
  background: var(--thumb-bg);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}
.progress-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 3px;
  transition: width 0.3s;
}
.progress-text {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 12px;
}
.claimed-btn {
  opacity: 0.7;
}
.ach-modal {
  text-align: center;
  max-width: 380px;
}
.ach-modal .modal-icon {
  font-size: 40px;
  margin: 8px 0;
}
.ach-modal h3 {
  margin: 0 0 12px;
  color: var(--primary-dark);
}
.ach-modal p {
  line-height: 1.7;
  margin-bottom: 20px;
}
</style>
