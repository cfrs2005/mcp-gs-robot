<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Tabs, Tab, Loading, showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import {
  getRobotStatus, getCapabilities, listMaps, getMapCanvas, listTaskDefinitions, listReports,
  startTask, pauseTask, resumeTask, stopTask, navigateHome, pageItems, isRobotUnreachable, robotErrorMessage,
  ApiError,
  type Robot, type RobotStatus, type RobotMap, type MapCanvas, type TaskDefinition, type TaskReport,
} from '@/api/client'
import { fleetRobot, loadFleet } from '@/api/fleet'
import { workStateName } from '@/shared/workStates'
import { area, duration, minutes, ratioPercent, timestamp } from '@/shared/format'
import { areaByDay, summarize } from '@/shared/reports'
import RobotImage from '@/components/ui/RobotImage.vue'
import BatteryBar from '@/components/ui/BatteryBar.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import KpiGrid, { type Kpi } from '@/components/ui/KpiGrid.vue'
import BarChart from '@/components/ui/BarChart.vue'
import MapThumb from '@/components/ui/MapThumb.vue'
import LocateCard from '@/components/cards/LocateCard.vue'
import { formatNumber, t, tn, type MessageKey } from '@/i18n'

const TABS = ['overview', 'maps', 'tasks', 'reports']
const route = useRoute()
const router = useRouter()
// The route component is reused between /robots/:sn pages, so sn is reactive and a change reloads everything.
const sn = ref(String(route.params.sn))
const initialTab = () => { const q = route.query.tab; return typeof q === 'string' && TABS.includes(q) ? q : 'overview' }
const tab = ref('overview')
const status = ref<RobotStatus | null>(null)
const goHome = () => {
  const mapId = status.value?.currentMapId
  if (!mapId) { showFailToast(t('detail.noMapForHome')); return }
  return action(t('detail.actionGoHome'), () => navigateHome(sn.value, mapId))
}
const maps = ref<RobotMap[]>([])
const canvas = ref<MapCanvas | null>(null)
const selectedMap = ref('')
const capabilities = ref<unknown>(null)
const definitions = ref<TaskDefinition[]>([])
const reports = ref<TaskReport[]>([])
const reportsPage = ref(1)
const moreReports = ref(false)
const loopCount = ref(1)
const busy = ref(false)
const loading = ref(false)
const tabLoading = ref(false)
// Offline (upstream 230003 or snapshot OFFLINE): explain in a top banner, hide live data, and do not chain toasts.
const offline = ref<{ traceId: string | null } | null>(null)
const info = ref<Robot | null>(null)
const isOnline = computed(() => status.value?.onlineStatus === 'ONLINE')

function markOffline(traceId: string | null = null) {
  offline.value = { traceId: traceId ?? offline.value?.traceId ?? null }
  status.value = null
}
function fail(e: unknown) {
  if (isRobotUnreachable(e)) { markOffline(e instanceof ApiError ? e.traceId : null); return }
  showFailToast(robotErrorMessage(e))
}
// Name / model / versions come from list_robots (shared cache); used by the hero and the offline panel.
async function loadInfo() {
  const target = sn.value
  try {
    await loadFleet()
    if (target === sn.value) info.value = fleetRobot(target) ?? null
  } catch { /* basic info is optional */ }
}
async function refreshStatus() {
  try {
    const target = sn.value
    const result = await getRobotStatus(target)
    if (target !== sn.value) return
    if (result.reachable === false || result.onlineStatus === 'OFFLINE') { markOffline(result.error?.trace_id ?? null); return }
    offline.value = null
    status.value = result
  } catch (e) { fail(e) }
}
async function loadTab(name: string) {
  tabLoading.value = true
  try {
    if (name === 'maps') maps.value = pageItems(await listMaps(sn.value))
    if (name === 'tasks') definitions.value = pageItems(await listTaskDefinitions(sn.value))
    if (name === 'reports') { reportsPage.value = 1; reports.value = []; await loadReports() }
  } catch (e) { fail(e) }
  finally { tabLoading.value = false }
}
async function loadReports() {
  const data = await listReports(sn.value, reportsPage.value)
  const items = pageItems(data)
  reports.value.push(...items)
  moreReports.value = items.length >= 20 && (Array.isArray(data) || reports.value.length < (data.count ?? data.totalSize ?? Infinity))
}
async function nextReports() {
  tabLoading.value = true
  try { reportsPage.value++; await loadReports() }
  catch (e) { reportsPage.value--; fail(e) }
  finally { tabLoading.value = false }
}
async function selectMap(mapId: string) {
  selectedMap.value = mapId
  canvas.value = null
  tabLoading.value = true
  try { canvas.value = await getMapCanvas(sn.value, mapId) } catch (e) { fail(e) }
  finally { tabLoading.value = false }
}
async function action(label: string, run: () => Promise<unknown>) {
  if (busy.value) return
  try { await showConfirmDialog({ title: t('detail.confirmTitle', { label }), message: t('detail.confirmMessage', { label, sn: sn.value }) }) }
  catch { return }
  busy.value = true
  try { await run(); showSuccessToast(t('detail.sent', { label })); await refreshStatus() }
  catch (e) { fail(e) }
  finally { busy.value = false }
}
function start(definition: TaskDefinition) {
  void action(tn('detail.actionStart', loopCount.value, { name: definition.taskName || t('detail.untitledTask') }), () => startTask(sn.value, definition.fusionTaskId, loopCount.value))
}
// Reports KPIs cover the reports loaded so far (the page count is shown next to them).
const reportKpis = computed<Kpi[]>(() => {
  const s = summarize(reports.value)
  const items: Kpi[] = [{ label: t('cards.tasks'), value: formatNumber(s.count) }]
  if (s.totalArea !== null) items.push({ label: t('cards.totalArea'), value: area(s.totalArea, 0), unit: 'm²' })
  if (s.avgDuration !== null) items.push({ label: t('cards.avgDuration'), value: minutes(s.avgDuration) })
  if (s.avgCompletion !== null) items.push({ label: t('cards.avgCompletion'), value: ratioPercent(s.avgCompletion) })
  return items
})
const reportDays = computed(() => areaByDay(reports.value))
// Capabilities as readable tags / fields: supportXxx 1 → "Supports Xxx", 0 → "No Xxx"; other values and
// unknown keys are shown as they are. The raw JSON stays in a collapsible block.
const CAP_LABELS: Record<string, MessageKey> = {
  productId: 'detail.cap.productId', robotFamilyCode: 'detail.cap.robotFamilyCode',
  FusionTask: 'detail.cap.FusionTask', TimerScheduleTask: 'detail.cap.TimerScheduleTask',
}
const words = (name: string) => name.replace(/([a-z0-9])([A-Z])/g, '$1 $2')
const capabilityView = computed(() => {
  const flags: { key: string; text: string; on: boolean | null }[] = []
  const fields: { key: string; label: string; value: string }[] = []
  const caps = capabilities.value
  if (!caps || typeof caps !== 'object' || Array.isArray(caps)) return { flags, fields }
  for (const [key, value] of Object.entries(caps as Record<string, unknown>)) {
    const support = /^support([A-Z]\w*)$/.exec(key)
    const text = typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value)
    if (support) {
      const name = CAP_LABELS[support[1]] ? t(CAP_LABELS[support[1]]) : words(support[1])
      const on = value === 1 || value === true ? true : value === 0 || value === false ? false : null
      flags.push({ key, on, text: on === true ? t('detail.capSupported', { name }) : on === false ? t('detail.capUnsupported', { name }) : `${name}: ${text}` })
    } else fields.push({ key, label: CAP_LABELS[key] ? t(CAP_LABELS[key]) : key, value: text })
  }
  return { flags, fields }
})
watch(tab, value => {
  if (value !== 'overview') void loadTab(value)
  if (route.query.tab !== value) void router.replace({ query: value === 'overview' ? {} : { tab: value } })
})
async function load() {
  const target = sn.value
  const wanted = initialTab()
  tab.value = 'overview'
  status.value = null; offline.value = null; info.value = null; capabilities.value = null
  maps.value = []; canvas.value = null; selectedMap.value = ''; definitions.value = []; reports.value = []; reportsPage.value = 1; moreReports.value = false
  loading.value = true
  void loadInfo()
  await refreshStatus()
  if (target !== sn.value) return
  if (!offline.value) {
    try { const result = await getCapabilities(target); if (target === sn.value) capabilities.value = result } catch (e) { if (target === sn.value) fail(e) }
  }
  loading.value = false
  tab.value = wanted
}
watch(() => route.query.tab, value => { if (!loading.value && typeof value === 'string' && TABS.includes(value) && value !== tab.value) tab.value = value })
watch(() => route.params.sn, value => {
  if (typeof value !== 'string' || value === sn.value) return
  sn.value = value
  void load()
})
onMounted(load)
</script>

<template>
  <div class="page detail">
    <section class="hero">
      <div class="hero-bar">
        <button type="button" class="hero-btn" :aria-label="t('detail.back')" @click="router.push('/robots')"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg></button>
        <span class="hero-title">{{ t('detail.title') }}</span>
        <button type="button" class="hero-btn text" @click="refreshStatus">{{ t('detail.refresh') }}</button>
      </div>
      <div class="identity">
        <div class="id-text">
          <strong>{{ sn }}</strong>
          <span v-if="info?.displayName && info.displayName !== sn" class="id-sub">{{ info.displayName }}</span>
          <span v-if="info?.modelTypeCode" class="id-sub">{{ t('detail.model', { value: info.modelTypeCode }) }}</span>
          <StatusPill :tone="isOnline ? 'ok' : 'off'" :label="isOnline ? t('robots.online') : t('robots.offline')" :solid="isOnline" class="id-pill" />
        </div>
        <RobotImage class="hero-photo" :info="info" :alt="sn" />
      </div>
      <div v-if="status" class="stats">
        <div class="stat"><BatteryBar :value="status.batteryPercent" :charging="status.charging" compact /><span>{{ t('robots.battery') }}<template v-if="status.charging"> {{ t('detail.charging') }}</template></span></div>
        <div class="stat"><b>{{ status.currentMapName || t('common.none') }}</b><span>{{ t('detail.statMap') }}</span></div>
        <div class="stat"><b>{{ workStateName(status) }}</b><span>{{ t('detail.statState') }}</span></div>
      </div>
    </section>
    <div v-if="offline" class="offline-banner" role="status"><strong>{{ t('detail.offlineTitle') }}</strong><span>{{ t('detail.offlineBody', { reason: t('errors.robotUnreachable') }) }}</span><span v-if="offline.traceId" class="muted trace">{{ t('detail.traceId', { id: offline.traceId }) }}</span></div>
    <Tabs v-model:active="tab" sticky class="detail-tabs">
      <Tab :title="t('detail.tabOverview')" name="overview">
        <div class="page-body">
          <div v-if="loading" class="empty"><Loading /> {{ t('common.loading') }}</div>
          <div v-else-if="offline && info" class="panel stack"><strong class="panel-title">{{ t('detail.basicInfo') }}</strong>
            <div>{{ t('detail.name', { value: String(info.displayName || info.name || '—') }) }}</div>
            <div>{{ t('detail.model', { value: info.modelTypeCode || '—' }) }}</div>
            <div>{{ t('detail.softwareVersion', { value: info.softwareVersion || '—' }) }}</div>
            <div>{{ t('detail.hardwareVersion', { value: info.hardwareVersion || '—' }) }}</div>
          </div>
          <div v-else-if="status" class="panel stack facts">
            <div>{{ t('detail.currentTask', { value: status.taskName || t('common.none') }) }}</div>
            <div class="muted">{{ t('detail.observedAt', { value: timestamp(status.observedMsTimestamp) }) }}</div>
          </div>
          <LocateCard v-if="!loading" class="locate" :sn="sn" :status="status" :offline="!!offline" @refresh="refreshStatus" />
          <div v-if="capabilities !== null" class="panel"><strong class="panel-title">{{ t('detail.capabilities') }}</strong>
            <div v-if="capabilityView.flags.length" class="cap-tags">
              <span v-for="flag in capabilityView.flags" :key="flag.key" class="cap-tag" :class="flag.on === true ? 'on' : flag.on === false ? 'off' : ''">{{ flag.text }}</span>
            </div>
            <dl v-if="capabilityView.fields.length" class="cap-fields">
              <template v-for="field in capabilityView.fields" :key="field.key"><dt>{{ field.label }}</dt><dd>{{ field.value }}</dd></template>
            </dl>
            <details class="cap-raw"><summary>{{ t('detail.capRaw') }}</summary><pre class="json">{{ JSON.stringify(capabilities, null, 2) }}</pre></details>
          </div>
          <div class="panel"><strong class="panel-title">{{ t('detail.quickActions') }}</strong><p class="muted">{{ t('detail.quickHint') }}</p><div class="action-grid">
            <Button size="small" type="primary" :disabled="busy" @click="tab = 'tasks'">{{ t('detail.pickTask') }}</Button>
            <Button size="small" :disabled="busy" @click="action(t('detail.actionPause'), () => pauseTask(sn))">{{ t('detail.pause') }}</Button>
            <Button size="small" :disabled="busy" @click="action(t('detail.actionResume'), () => resumeTask(sn))">{{ t('detail.resume') }}</Button>
            <Button size="small" type="danger" plain :disabled="busy" @click="action(t('detail.actionStop'), () => stopTask(sn))">{{ t('detail.stop') }}</Button>
            <Button size="small" :disabled="busy" @click="goHome()">{{ t('detail.goHome') }}</Button>
          </div></div>
        </div>
      </Tab>
      <Tab :title="t('detail.tabMaps')" name="maps"><div class="page-body">
        <div v-if="!maps.length && !tabLoading" class="empty">{{ offline ? t('detail.mapsOffline') : t('detail.noMaps') }}</div>
        <div v-if="maps.length" class="map-list">
          <button v-for="map in maps" :key="map.mapId" class="map-button" :class="{ on: selectedMap === map.mapId }" type="button" @click="selectMap(map.mapId)">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6.5l6-2.5 6 2.5 6-2.5v13.5l-6 2.5-6-2.5-6 2.5z" /><path d="M9 4v13.5M15 6.5V20" /></svg><span>{{ map.displayName || map.mapId }}</span>
          </button>
        </div>
        <div v-if="tabLoading" class="empty"><Loading /> {{ t('common.loading') }}</div>
        <div v-if="canvas" class="panel"><strong class="panel-title">{{ t('detail.canvas') }}</strong><MapThumb tall :src="canvas.mapPng?.exist && canvas.mapPng.downloadUri ? canvas.mapPng.downloadUri : null" /><p v-if="canvas.mapInfo" class="muted map-info">{{ t('detail.mapInfo', { w: canvas.mapInfo.gridWidth ?? '—', h: canvas.mapInfo.gridHeight ?? '—', r: canvas.mapInfo.resolution ?? '—', x: canvas.mapInfo.originX ?? '—', y: canvas.mapInfo.originY ?? '—' }) }}</p></div>
      </div></Tab>
      <Tab :title="t('detail.tabTasks')" name="tasks"><div class="page-body">
        <div class="panel row between"><span>{{ t('detail.loopCount') }}</span><select v-model.number="loopCount" :aria-label="t('detail.loopCount')"><option v-for="n in [1, 2, 3]" :key="n" :value="n">{{ tn('detail.loopOption', n) }}</option></select></div>
        <div v-if="!definitions.length && !tabLoading" class="empty">{{ offline ? t('detail.tasksOffline') : t('detail.noTasks') }}</div>
        <div v-for="definition in definitions" :key="definition.fusionTaskId" class="panel row between task"><div class="task-text"><strong>{{ definition.taskName || t('detail.untitledTask') }}</strong><div class="muted id">{{ definition.fusionTaskId }}</div></div><Button size="small" type="primary" :disabled="busy" @click="start(definition)">{{ t('detail.start') }}</Button></div>
        <div v-if="tabLoading" class="empty"><Loading /> {{ t('common.loading') }}</div>
      </div></Tab>
      <Tab :title="t('detail.tabReports')" name="reports"><div class="page-body">
        <div v-if="reports.length" class="panel stack">
          <div class="row between"><strong class="panel-title flush">{{ t('detail.reportsSummary') }}</strong><span class="muted">{{ tn('detail.reportsLoaded', reports.length) }}</span></div>
          <KpiGrid :items="reportKpis" />
          <template v-if="reportDays.length"><span class="muted">{{ t('cards.areaTrend') }}</span><BarChart :points="reportDays" unit="m²" :title="t('cards.areaTrend')" /></template>
        </div>
        <div v-if="!reports.length && !tabLoading" class="empty">{{ t('detail.noReports') }}</div>
        <div v-for="(report, index) in reports" :key="report.id || index" class="panel report">
          <div class="r-head"><strong>{{ report.displayName || t('detail.untitledTask') }}</strong><span v-if="report.cleaningMode" class="r-mode">{{ report.cleaningMode }}</span></div>
          <span class="muted">{{ timestamp(report.startTime) }} — {{ timestamp(report.endTime) }}</span>
          <span class="r-line">{{ t('detail.reportLine', { area: area(report.actualCleaningAreaSquareMeter), duration: duration(report.durationSeconds), completion: ratioPercent(report.completionPercentage) }) }}</span>
        </div>
        <div v-if="tabLoading" class="empty"><Loading /> {{ t('common.loading') }}</div>
        <Button v-if="moreReports && !tabLoading" block plain round type="primary" @click="nextReports">{{ t('detail.loadMore') }}</Button>
      </div></Tab>
    </Tabs>
  </div>
</template>

<style scoped>
.hero { margin: 0 0 4px; padding: 10px 16px 16px; border-radius: 0 0 var(--sd-r-xl) var(--sd-r-xl); background: var(--sd-hero-grad); color: var(--sd-on-primary); box-shadow: var(--sd-shadow-2); }
.hero-bar { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 40px; }
.hero-title { font-size: var(--sd-fs-sm); font-weight: 600; opacity: .85; }
.hero-btn { display: grid; place-items: center; min-width: 34px; height: 34px; padding: 0 10px; border: 0; border-radius: var(--sd-r-pill); background: var(--sd-glow); color: var(--sd-on-primary); font-size: var(--sd-fs-sm); font-weight: 600; cursor: pointer; }
.hero-btn svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
.identity { display: flex; align-items: center; gap: 12px; margin-top: 6px; }
.id-text { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; gap: 3px; }
.id-text strong { font-size: var(--sd-fs-lg); line-height: 1.3; overflow-wrap: anywhere; }
.id-sub { font-size: var(--sd-fs-xs); opacity: .85; overflow-wrap: anywhere; }
.id-pill { margin-top: 5px; }
.hero-photo { flex: none; width: 116px; height: 104px; border-radius: var(--sd-r-lg); background: var(--sd-surface); }
.stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }
.stat { display: flex; flex-direction: column; justify-content: center; gap: 3px; min-width: 0; padding: 10px; border-radius: var(--sd-r-md); background: var(--sd-surface); color: var(--sd-ink); }
.stat b { font-size: var(--sd-fs-sm); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stat span { font-size: var(--sd-fs-2xs); color: var(--sd-muted); }
.stat :deep(.num) { text-align: left; font-size: var(--sd-fs-sm); }
.offline-banner { display: flex; flex-direction: column; gap: 4px; margin: 12px 14px 4px; padding: 12px 14px; border-radius: var(--sd-r-md); background: var(--sd-warning-soft); border: 1px solid var(--sd-warning-line); color: var(--sd-warning); font-size: var(--sd-fs-sm); }
.offline-banner .trace { overflow-wrap: anywhere; font-size: var(--sd-fs-xs); }
.detail-tabs :deep(.van-tabs__wrap) { background: var(--sd-bg); }
.detail-tabs :deep(.van-tab--active) { font-weight: 700; }
.facts { font-size: var(--sd-fs-md); color: var(--sd-ink-2); }
.locate { margin-bottom: 12px; }
.battery-line { display: grid; gap: 6px; }
.panel-title { display: block; }
.panel-title.flush { margin: 0; }
.action-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
.map-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-bottom: 12px; }
.map-button { display: flex; align-items: center; gap: 8px; min-width: 0; padding: 12px; border: 0; border-radius: var(--sd-r-md); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); text-align: left; color: var(--sd-ink); font-size: var(--sd-fs-sm); font-weight: 600; cursor: pointer; }
.map-button span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.map-button svg { width: 18px; height: 18px; flex: none; fill: none; stroke: var(--sd-primary); stroke-width: 2; stroke-linejoin: round; }
.map-button.on { background: var(--sd-primary-soft); box-shadow: inset 0 0 0 1.5px var(--sd-primary); }
.map-info { margin: 10px 0 0; }
.task-text { min-width: 0; }
.task .id { overflow-wrap: anywhere; font-size: var(--sd-fs-xs); }
.report { display: grid; gap: 4px; }
.r-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.r-head strong { color: var(--sd-ink); }
.r-mode { flex: none; padding: 2px 8px; border-radius: var(--sd-r-pill); background: var(--sd-primary-soft); color: var(--sd-primary); font-size: var(--sd-fs-xs); font-weight: 600; }
.r-line { font-size: var(--sd-fs-sm); color: var(--sd-ink-2); }
.cap-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.cap-tag { padding: 4px 10px; border-radius: var(--sd-r-pill); background: var(--sd-surface-2); box-shadow: inset 0 0 0 1px var(--sd-line); color: var(--sd-ink-2); font-size: var(--sd-fs-xs); font-weight: 600; }
.cap-tag.on { background: var(--sd-success-soft); box-shadow: none; color: var(--sd-success); }
.cap-tag.off { color: var(--sd-muted); }
.cap-fields { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 6px 14px; margin: 12px 0 0; font-size: var(--sd-fs-sm); }
.cap-fields dt { color: var(--sd-muted); }
.cap-fields dd { margin: 0; color: var(--sd-ink); overflow-wrap: anywhere; }
.cap-raw { margin-top: 12px; }
.cap-raw summary { cursor: pointer; color: var(--sd-primary); font-size: var(--sd-fs-xs); font-weight: 600; }
.cap-raw .json { margin-top: 8px; }
.json { max-height: 160px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-size: var(--sd-fs-xs); margin: 0; padding: 10px; border-radius: var(--sd-r-sm); background: var(--sd-surface-2); }
select { background: var(--sd-surface); border: 1px solid var(--sd-line-strong); border-radius: var(--sd-r-xs); padding: 6px 8px; color: var(--sd-ink); }
</style>
