<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PullRefresh, Loading, showFailToast } from 'vant'
import { messageForCode, robotErrorMessage } from '@/api/client'
import { fleetState, fleetSummary, loadFleetStatus, useFleet, type FleetRobot } from '@/api/fleet'
import { workStateName } from '@/shared/workStates'
import RobotImage from '@/components/ui/RobotImage.vue'
import BatteryBar from '@/components/ui/BatteryBar.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import { formatNumber, t } from '@/i18n'

type Card = FleetRobot

const router = useRouter()
const fleet = useFleet()
// The list and every count come from api/fleet.ts (same source as the chat home overview).
const robots = computed(() => fleet.cards)
const summary = fleetSummary()
const refreshing = ref(false)
const loading = ref(false)
const error = ref('')
const query = ref('')
const filter = ref('all')

const reachable = (robot: Card) => fleetState(robot) === 'online'
function tagText(robot: Card): string {
  const state = fleetState(robot)
  return state === 'online' ? t('robots.online') : state === 'unreachable' ? t('robots.unreachable') : t('robots.offline')
}
function statusText(robot: Card): string {
  const state = fleetState(robot)
  if (state === 'online') return workStateName(robot)
  // Localize by error.code; the server's message is only a fallback for codes the UI does not know.
  if (state === 'unreachable' && robot.reachable === false) return t('robots.statusUnreachable', { message: messageForCode(robot.error?.code ?? 230003, robot.error?.message) })
  return t('robots.statusOffline')
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    await loadFleetStatus(true)
  } catch (e) {
    error.value = robotErrorMessage(e) || t('robots.loadFailed')
    showFailToast(error.value)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}
onMounted(load)

// Filters use only data already on the page: online flag, live work state, charging flag.
type Chip = { key: string; label: string; count: number; test: (r: Card) => boolean }
const chips = computed<Chip[]>(() => {
  const base: Chip[] = [
    { key: 'all', label: t('robots.filterAll'), count: robots.value.length, test: () => true },
    { key: 'online', label: t('robots.online'), count: summary.value?.online ?? 0, test: reachable },
    { key: 'offline', label: t('robots.offline'), count: summary.value?.offline ?? 0, test: r => fleetState(r) === 'offline' },
  ]
  if (summary.value?.unreachable) base.push({ key: 'unreachable', label: t('robots.unreachable'), count: summary.value.unreachable, test: r => fleetState(r) === 'unreachable' })
  const states = new Map<string, number>()
  for (const r of robots.value) if (reachable(r) && r.workState !== undefined) { const name = workStateName(r); states.set(name, (states.get(name) ?? 0) + 1) }
  const byState = [...states.entries()].sort((a, b) => b[1] - a[1]).map(([name, count]) => ({ key: `state:${name}`, label: name, count, test: (r: Card) => reachable(r) && r.workState !== undefined && workStateName(r) === name }))
  const charging = robots.value.filter(r => reachable(r) && r.charging).length
  return [...base, ...byState, ...(charging ? [{ key: 'charging', label: t('robots.filterCharging'), count: charging, test: (r: Card) => reachable(r) && !!r.charging }] : [])]
})
const shown = computed(() => {
  const chip = chips.value.find(c => c.key === filter.value) ?? chips.value[0]
  const q = query.value.trim().toLowerCase()
  return robots.value.filter(r => chip.test(r) && (!q || [r.robotSn, r.displayName, r.currentMapName].some(v => typeof v === 'string' && v.toLowerCase().includes(q))))
})
</script>

<template>
  <div class="page">
    <header class="page-header robots-head">
      <div><h1>{{ t('robots.title') }}</h1><p v-if="summary" class="muted">{{ t('robots.summary', { total: formatNumber(summary.total), online: formatNumber(summary.online) }) }}<template v-if="summary.unreachable"> · <span class="unreachable">{{ t('robots.unreachableCount', { n: formatNumber(summary.unreachable) }) }}</span></template></p></div>
    </header>
    <div class="tools">
      <label class="search">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="M16 16l4 4" /></svg>
        <input v-model="query" type="search" :placeholder="t('robots.searchPlaceholder')" :aria-label="t('robots.searchPlaceholder')">
      </label>
      <div class="chips" role="tablist">
        <button v-for="chip in chips" :key="chip.key" type="button" role="tab" class="chip" :class="{ on: filter === chip.key }" :aria-selected="filter === chip.key" @click="filter = chip.key">{{ chip.label }}<b>{{ formatNumber(chip.count) }}</b></button>
      </div>
    </div>
    <PullRefresh v-model="refreshing" @refresh="load">
      <div class="page-body list">
        <div v-if="loading && !refreshing && !robots.length" class="empty"><Loading /> {{ t('common.loading') }}</div>
        <div v-else-if="!robots.length" class="empty">{{ error || t('robots.empty') }}</div>
        <div v-else-if="!shown.length" class="empty">{{ t('robots.noMatch') }}</div>
        <button v-for="robot in shown" :key="robot.robotSn" class="robot-card" :class="{ inactive: !reachable(robot) }" type="button" @click="router.push(`/robots/${encodeURIComponent(robot.robotSn)}`)">
          <RobotImage class="photo" :info="robot" :alt="robot.robotSn" />
          <div class="info">
            <div class="line1"><strong class="sn">{{ robot.robotSn }}</strong><StatusPill :tone="reachable(robot) ? 'ok' : fleetState(robot) === 'unreachable' ? 'warn' : 'off'" :label="tagText(robot)" :solid="reachable(robot)" /></div>
            <div v-if="robot.displayName && robot.displayName !== robot.robotSn" class="name">{{ robot.displayName }}<template v-if="robot.modelTypeCode"> · {{ robot.modelTypeCode }}</template></div>
            <p class="fact"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="7.5" /><path d="M12 8v4l2.5 2" /></svg>{{ t('robots.status', { value: statusText(robot) }) }} <span v-if="reachable(robot) && robot.charging">{{ t('robots.charging') }}</span></p>
            <div class="bottom">
              <p class="fact map"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6.5l6-2.5 6 2.5 6-2.5v13.5l-6 2.5-6-2.5-6 2.5z" /></svg>{{ t('robots.map', { value: reachable(robot) ? robot.currentMapName || t('common.none') : '—' }) }}</p>
              <BatteryBar class="battery" :value="reachable(robot) ? robot.batteryPercent : null" :charging="reachable(robot) && robot.charging" :aria-label="t('robots.battery')" />
            </div>
          </div>
          <svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
        </button>
        <div v-if="loading && robots.length && !refreshing" class="empty small"><Loading size="16" /> {{ t('common.loading') }}</div>
      </div>
    </PullRefresh>
  </div>
</template>

<style scoped>
.robots-head { align-items: flex-end; padding-top: 18px; }
.robots-head h1 { margin: 0; font-size: var(--sd-fs-2xl); line-height: 1.2; }
.robots-head p { margin: 4px 0 0; font-weight: 500; }
.robots-head .unreachable { color: var(--sd-warning); }
.tools { position: sticky; top: 0; z-index: 5; display: grid; gap: 10px; padding: 8px 14px 10px; background: color-mix(in srgb, var(--sd-bg) 92%, transparent); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
.search { display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 14px; border-radius: var(--sd-r-md); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); }
.search svg { width: 18px; height: 18px; flex: none; fill: none; stroke: var(--sd-muted); stroke-width: 2; stroke-linecap: round; }
.search input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--sd-ink); font-size: var(--sd-fs-md); }
.search input::placeholder { color: var(--sd-faint); }
.chips { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; margin: 0 -14px; padding: 0 14px; }
.chips::-webkit-scrollbar { display: none; }
.chip { flex: none; display: inline-flex; align-items: center; gap: 6px; height: 32px; padding: 0 12px; border: 1px solid var(--sd-line-strong); border-radius: var(--sd-r-pill); background: var(--sd-surface); color: var(--sd-ink-2); font-size: var(--sd-fs-sm); cursor: pointer; white-space: nowrap; }
.chip b { font-weight: 600; color: var(--sd-muted); font-variant-numeric: tabular-nums; }
.chip.on { border-color: var(--sd-primary); background: var(--sd-primary); color: var(--sd-on-primary); }
.chip.on b { color: var(--sd-on-primary); opacity: .85; }
.list { display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 10px; padding-top: 4px; }
.robot-card { display: flex; align-items: center; gap: 10px; width: 100%; padding: 12px 10px 12px 12px; border: 0; border-radius: var(--sd-r-lg); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); text-align: left; color: inherit; cursor: pointer; }
.photo { flex: none; width: 66px; height: 66px; border-radius: var(--sd-r-md); background: var(--sd-primary-softer); }
.info { flex: 1; min-width: 0; display: grid; gap: 5px; }
.line1 { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; min-width: 0; }
.sn { min-width: 0; font-size: var(--sd-fs-sm); letter-spacing: -.1px; color: var(--sd-ink); overflow-wrap: anywhere; }
.name { font-size: var(--sd-fs-xs); color: var(--sd-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fact { display: flex; align-items: center; gap: 5px; margin: 0; min-width: 0; font-size: var(--sd-fs-sm); color: var(--sd-ink-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fact svg { width: 15px; height: 15px; flex: none; fill: none; stroke: var(--sd-muted); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.bottom { display: flex; align-items: center; gap: 10px; min-width: 0; }
.bottom .map { flex: 1; }
.battery { flex: none; width: 92px; }
.chev { width: 14px; height: 14px; flex: none; fill: none; stroke: var(--sd-faint); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.robot-card.inactive { background: var(--sd-surface-2); box-shadow: inset 0 0 0 1px var(--sd-line); }
.robot-card.inactive .sn { color: var(--sd-ink-2); }
.robot-card.inactive .photo { opacity: .6; filter: grayscale(.6); }
.empty.small { padding: 10px; }
</style>
