<script setup>
defineProps({ art: { type: String, default: '' } })
</script>

<template>
  <svg v-if="art === 'basket'" class="ach-art" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
    <rect x="20" y="35" width="80" height="35" rx="4" fill="none" stroke="currentColor" stroke-width="2"/>
    <path d="M30 35 Q60 10 90 35" fill="none" stroke="currentColor" stroke-width="2"/>
    <line x1="45" y1="50" x2="75" y2="50" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>
  </svg>
  <svg v-else-if="art === 'cabinet'" class="ach-art" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
    <rect x="25" y="15" width="70" height="55" rx="3" fill="none" stroke="currentColor" stroke-width="2"/>
    <line x1="25" y1="42" x2="95" y2="42" stroke="currentColor" stroke-width="1.5"/>
    <line x1="60" y1="15" x2="60" y2="70" stroke="currentColor" stroke-width="1.5"/>
    <circle cx="52" cy="28" r="2" fill="currentColor" opacity="0.6"/>
    <circle cx="68" cy="28" r="2" fill="currentColor" opacity="0.6"/>
  </svg>
  <svg v-else-if="art === 'courtyard'" class="ach-art" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 55 L60 25 L110 55 Z" fill="none" stroke="currentColor" stroke-width="2"/>
    <rect x="40" y="45" width="40" height="25" fill="none" stroke="currentColor" stroke-width="2"/>
    <circle cx="95" cy="20" r="10" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>
  </svg>
  <svg v-else-if="art === 'labels'" class="ach-art" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
    <rect x="15" y="20" width="35" height="22" rx="3" fill="none" stroke="currentColor" stroke-width="2"/>
    <rect x="55" y="30" width="35" height="22" rx="3" fill="none" stroke="currentColor" stroke-width="2"/>
    <rect x="35" y="48" width="35" height="22" rx="3" fill="none" stroke="currentColor" stroke-width="2"/>
  </svg>
  <svg v-else-if="art === 'shelves'" class="ach-art" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
    <rect x="30" y="12" width="60" height="58" fill="none" stroke="currentColor" stroke-width="2"/>
    <line x1="30" y1="32" x2="90" y2="32" stroke="currentColor" stroke-width="1.5"/>
    <line x1="30" y1="52" x2="90" y2="52" stroke="currentColor" stroke-width="1.5"/>
    <rect x="38" y="18" width="14" height="10" fill="currentColor" opacity="0.2"/>
    <rect x="58" y="38" width="20" height="10" fill="currentColor" opacity="0.2"/>
  </svg>
  <svg v-else-if="art === 'planner'" class="ach-art" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
    <rect x="15" y="18" width="90" height="50" rx="4" fill="none" stroke="currentColor" stroke-width="2"/>
    <line x1="15" y1="35" x2="105" y2="35" stroke="currentColor" stroke-width="1"/>
    <rect x="25" y="42" width="18" height="18" fill="currentColor" opacity="0.15"/>
    <rect x="50" y="42" width="18" height="18" fill="currentColor" opacity="0.15"/>
    <rect x="75" y="42" width="18" height="18" fill="currentColor" opacity="0.15"/>
  </svg>
  <div v-else class="ach-art-fallback">🏅</div>
</template>

<style scoped>
.ach-art {
  width: 100%;
  max-width: 140px;
  height: auto;
  color: var(--primary);
  opacity: 0.85;
}
.ach-art-fallback {
  font-size: 48px;
  text-align: center;
}
</style>
