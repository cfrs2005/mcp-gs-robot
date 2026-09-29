<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fleetSummary, loadFleetStatus, useFleet } from '@/api/fleet'
import markUrl from '@/shared/mark.svg'
import { STARTERS } from './followUps'
import { formatNumber, t } from '@/i18n'

// Empty-chat home: hero, suggested questions, and fleet counts from api/fleet.ts fleetSummary() —
// the same list_robots + live status source and state definitions as the robot list page.
// No per-robot report calls here.
const emit = defineEmits<{ ask: [text: string] }>()
const router = useRouter()
const fleet = useFleet()
const summary = fleetSummary()
onMounted(() => { loadFleetStatus().catch(() => undefined) })
</script>

<template>
  <div class="welcome">
    <section class="hero">
      <img :src="markUrl" alt="" class="hero-mark">
      <div class="hero-text">
        <h1>{{ t('home.hello') }}</h1>
        <p>{{ t('chat.welcome') }}</p>
      </div>
    </section>

    <section class="block">
      <h2>{{ t('home.tryAsking') }}</h2>
      <div class="starters">
        <button v-for="s in STARTERS" :key="s.key" type="button" class="starter" @click="emit('ask', t(s.key))">
          <span class="s-icon" :class="s.icon" aria-hidden="true">
            <svg v-if="s.icon === 'alert'" viewBox="0 0 24 24"><path d="M12 4l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
            <svg v-else-if="s.icon === 'chart'" viewBox="0 0 24 24"><path d="M6 19V11M12 19V5M18 19v-6" /></svg>
            <svg v-else-if="s.icon === 'battery'" viewBox="0 0 24 24"><rect x="3" y="7" width="16" height="10" rx="2.5" /><path d="M21 10.5v3M7 12h5" /></svg>
            <svg v-else viewBox="0 0 24 24"><path d="M3 6.5l6-2.5 6 2.5 6-2.5v13.5l-6 2.5-6-2.5-6 2.5z" /><path d="M9 4v13.5M15 6.5V20" /></svg>
          </span>
          <span class="s-text">{{ t(s.key) }}</span>
        </button>
      </div>
    </section>

    <section class="block fleet">
      <div class="fleet-head"><h2>{{ t('home.fleet') }}</h2><button type="button" class="link" @click="router.push('/robots')">{{ t('home.viewAll') }} ›</button></div>
      <div v-if="summary" class="fleet-stats" :class="{ four: summary.unreachable }">
        <div><b>{{ formatNumber(summary.total) }}</b><span>{{ t('home.totalRobots') }}</span></div>
        <div class="on"><b>{{ formatNumber(summary.online) }}</b><span>{{ t('robots.online') }}</span></div>
        <div><b>{{ formatNumber(summary.offline) }}</b><span>{{ t('robots.offline') }}</span></div>
        <div v-if="summary.unreachable" class="warn"><b>{{ formatNumber(summary.unreachable) }}</b><span>{{ t('robots.unreachable') }}</span></div>
      </div>
      <p v-else class="fleet-note">{{ fleet.statusFailed ? t('robots.loadFailed') : t('common.loading') }}</p>
    </section>
  </div>
</template>

<style scoped>
.welcome { display: grid; gap: 14px; padding-top: 4px; }
.hero { position: relative; display: flex; align-items: center; gap: 14px; padding: 20px 18px; border-radius: var(--sd-r-xl); background: var(--sd-hero-grad); color: var(--sd-on-primary); box-shadow: var(--sd-shadow-2); overflow: hidden; }
.hero::after { content: ''; position: absolute; right: -40px; top: -50px; width: 170px; height: 170px; border-radius: 50%; background: radial-gradient(circle, var(--sd-glow), transparent 70%); }
.hero-mark { width: 68px; height: 68px; flex: none; padding: 6px; border-radius: var(--sd-r-lg); background: var(--sd-surface); }
.hero-text { min-width: 0; }
.hero h1 { margin: 0; font-size: var(--sd-fs-xl); line-height: 1.25; }
.hero p { margin: 5px 0 0; font-size: var(--sd-fs-sm); line-height: 1.5; opacity: .9; }
.block { padding: 14px; border-radius: var(--sd-r-lg); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); }
.block h2 { margin: 0 0 10px; font-size: var(--sd-fs-md); color: var(--sd-ink); }
.starters { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.starter { display: flex; align-items: center; gap: 9px; min-height: 58px; padding: 10px; border: 0; border-radius: var(--sd-r-md); background: var(--sd-surface-2); box-shadow: inset 0 0 0 1px var(--sd-line); color: var(--sd-ink); text-align: left; font-size: var(--sd-fs-sm); line-height: 1.35; cursor: pointer; }
.starter:active { background: var(--sd-primary-soft); }
.s-icon { flex: none; display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%; background: var(--sd-primary-soft); }
.s-icon svg { width: 18px; height: 18px; fill: none; stroke: var(--sd-primary); stroke-width: 2.1; stroke-linecap: round; stroke-linejoin: round; }
.s-icon.alert { background: var(--sd-warning-soft); }
.s-icon.alert svg { stroke: var(--sd-warning); }
.s-icon.battery { background: var(--sd-success-soft); }
.s-icon.battery svg { stroke: var(--sd-success); }
.fleet-head { display: flex; align-items: baseline; justify-content: space-between; }
.link { border: 0; background: transparent; color: var(--sd-primary); font-size: var(--sd-fs-sm); cursor: pointer; }
.fleet-stats { display: grid; grid-template-columns: repeat(3, 1fr); }
.fleet-stats.four { grid-template-columns: repeat(4, 1fr); }
.fleet-stats div.warn { border-left-color: var(--sd-warning); }
.fleet-stats div.warn b { color: var(--sd-warning); }
.fleet-stats div { display: flex; flex-direction: column; gap: 2px; padding-left: 12px; border-left: 3px solid var(--sd-line); }
.fleet-stats div.on { border-left-color: var(--sd-success); }
.fleet-stats b { font-size: var(--sd-fs-2xl); line-height: 1.1; color: var(--sd-ink); font-variant-numeric: tabular-nums; }
.fleet-stats div.on b { color: var(--sd-success); }
.fleet-stats span { font-size: var(--sd-fs-xs); color: var(--sd-muted); }
.fleet-note { margin: 0; font-size: var(--sd-fs-sm); color: var(--sd-muted); }
</style>
