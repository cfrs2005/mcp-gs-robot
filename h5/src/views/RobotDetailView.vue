<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Tabs, Tab, Tag, Progress, Loading, showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import {
  getRobotStatus, getCapabilities, listMaps, getMapCanvas, listTaskDefinitions, listReports, listRobots,
  startTask, pauseTask, resumeTask, stopTask, navigateHome, pageItems, isRobotUnreachable, robotErrorMessage,
  ApiError,
  type Robot, type RobotStatus, type RobotMap, type MapCanvas, type TaskDefinition, type TaskReport,
} from '@/api/client'
import { workStateName } from '@/workStates'
import { formatDateTime, formatNumber, t, tn } from '@/i18n'

const route = useRoute()
const router = useRouter()
// The route component is reused between /robots/:sn pages, so sn is reactive and a change reloads everything.
const sn = ref(String(route.params.sn))
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

function markOffline(traceId: string | null = null) {
  offline.value = { traceId: traceId ?? offline.value?.traceId ?? null }
  status.value = null
  if (!info.value) void loadInfo()
}
function fail(e: unknown) {
  if (isRobotUnreachable(e)) { markOffline(e instanceof ApiError ? e.traceId : null); return }
  showFailToast(robotErrorMessage(e))
}
async function loadInfo() {
  const target = sn.value
  try {
    const found = pageItems(await listRobots()).find(item => item.robotSn === target) ?? null
    if (target === sn.value) info.value = found
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
function timestamp(value?: number): string {
  if (!value) return '—'
  const date = new Date(value < 1e11 ? value * 1000 : value)
  return Number.isNaN(date.getTime()) ? '—' : formatDateTime(date, { dateStyle: 'medium', timeStyle: 'medium', hour12: false })
}
function duration(seconds?: number): string {
  return seconds === undefined ? '—' : formatNumber(Math.round(seconds / 60), { style: 'unit', unit: 'minute', unitDisplay: 'long' })
}
// completionPercentage is a 0–1 ratio upstream (0.91 → 91%), unlike batteryPercent which is 0–100.
function ratioPercent(value?: number | null): string { return value == null ? '—' : formatNumber(value, { style: 'percent', maximumFractionDigits: 0 }) }
const area = (value?: number) => value == null ? '—' : formatNumber(value, { maximumFractionDigits: 2 })
watch(tab, value => { if (value !== 'overview') void loadTab(value) })
async function load() {
  const target = sn.value
  tab.value = 'overview'
  status.value = null; offline.value = null; info.value = null; capabilities.value = null
  maps.value = []; canvas.value = null; selectedMap.value = ''; definitions.value = []; reports.value = []; reportsPage.value = 1; moreReports.value = false
  loading.value = true
  await refreshStatus()
  if (target !== sn.value) return
  if (!offline.value) {
    try { const result = await getCapabilities(target); if (target === sn.value) capabilities.value = result } catch (e) { if (target === sn.value) fail(e) }
  }
  loading.value = false
}
watch(() => route.params.sn, value => {
  if (typeof value !== 'string' || value === sn.value) return
  sn.value = value
  void load()
})
onMounted(load)
</script>

<template>
  <div class="page">
    <header class="page-header"><div class="row"><Button icon="arrow-left" size="small" plain @click="router.push('/robots')" />{{ t('detail.title') }}</div><Button size="small" plain @click="refreshStatus">{{ t('detail.refresh') }}</Button></header>
    <div class="identity"><strong>{{ sn }}</strong><Tag :type="status?.onlineStatus === 'ONLINE' ? 'success' : 'default'">{{ status?.onlineStatus === 'ONLINE' ? t('robots.online') : t('robots.offline') }}</Tag></div>
    <div v-if="offline" class="offline-banner" role="status"><strong>{{ t('detail.offlineTitle') }}</strong><span>{{ t('detail.offlineBody', { reason: t('errors.robotUnreachable') }) }}</span><span v-if="offline.traceId" class="muted trace">{{ t('detail.traceId', { id: offline.traceId }) }}</span></div>
    <Tabs v-model:active="tab" sticky>
      <Tab :title="t('detail.tabOverview')" name="overview">
        <div class="page-body">
          <div v-if="loading" class="empty"><Loading /> {{ t('common.loading') }}</div>
          <div v-else-if="offline && info" class="panel stack"><strong>{{ t('detail.basicInfo') }}</strong>
            <div>{{ t('detail.name', { value: String(info.displayName || info.name || '—') }) }}</div>
            <div>{{ t('detail.model', { value: info.modelTypeCode || '—' }) }}</div>
            <div>{{ t('detail.softwareVersion', { value: info.softwareVersion || '—' }) }}</div>
            <div>{{ t('detail.hardwareVersion', { value: info.hardwareVersion || '—' }) }}</div>
          </div>
          <div v-else-if="status" class="panel stack">
            <div>{{ t('detail.workState', { value: workStateName(status) }) }}</div>
            <div>{{ t('detail.currentMap', { value: status.currentMapName || t('common.none') }) }}</div>
            <div>{{ t('detail.currentTask', { value: status.taskName || t('common.none') }) }}</div>
            <div>{{ t('detail.battery', { value: status.batteryPercent ?? '—' }) }} <span v-if="status.charging">{{ t('detail.charging') }}</span><Progress :percentage="status.batteryPercent ?? 0" :show-pivot="false" /></div>
            <div class="muted">{{ t('detail.observedAt', { value: timestamp(status.observedMsTimestamp) }) }}</div>
          </div>
          <div v-if="capabilities !== null" class="panel"><strong>{{ t('detail.capabilities') }}</strong><pre class="json">{{ JSON.stringify(capabilities, null, 2) }}</pre></div>
          <div class="panel"><strong>{{ t('detail.quickActions') }}</strong><p class="muted">{{ t('detail.quickHint') }}</p><div class="action-grid">
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
        <button v-for="map in maps" :key="map.mapId" class="panel map-button" type="button" @click="selectMap(map.mapId)">{{ map.displayName || map.mapId }}</button>
        <div v-if="tabLoading" class="empty"><Loading /> {{ t('common.loading') }}</div>
        <div v-if="canvas" class="panel"><strong>{{ t('detail.canvas') }}</strong><img v-if="canvas.mapPng?.exist && canvas.mapPng.downloadUri" class="map-image" :src="canvas.mapPng.downloadUri" :alt="t('detail.canvas')" /><p v-else class="muted">{{ t('detail.noMapImage') }}</p><p v-if="canvas.mapInfo" class="muted">{{ t('detail.mapInfo', { w: canvas.mapInfo.gridWidth ?? '—', h: canvas.mapInfo.gridHeight ?? '—', r: canvas.mapInfo.resolution ?? '—', x: canvas.mapInfo.originX ?? '—', y: canvas.mapInfo.originY ?? '—' }) }}</p></div>
      </div></Tab>
      <Tab :title="t('detail.tabTasks')" name="tasks"><div class="page-body">
        <div class="panel row"><span>{{ t('detail.loopCount') }}</span><select v-model.number="loopCount" :aria-label="t('detail.loopCount')"><option v-for="n in [1, 2, 3]" :key="n" :value="n">{{ tn('detail.loopOption', n) }}</option></select></div>
        <div v-if="!definitions.length && !tabLoading" class="empty">{{ offline ? t('detail.tasksOffline') : t('detail.noTasks') }}</div>
        <div v-for="definition in definitions" :key="definition.fusionTaskId" class="panel row between"><div><strong>{{ definition.taskName || t('detail.untitledTask') }}</strong><div class="muted">{{ definition.fusionTaskId }}</div></div><Button size="small" type="primary" :disabled="busy" @click="start(definition)">{{ t('detail.start') }}</Button></div>
        <div v-if="tabLoading" class="empty"><Loading /> {{ t('common.loading') }}</div>
      </div></Tab>
      <Tab :title="t('detail.tabReports')" name="reports"><div class="page-body">
        <div v-if="!reports.length && !tabLoading" class="empty">{{ t('detail.noReports') }}</div>
        <div v-for="(report, index) in reports" :key="report.id || index" class="panel stack"><strong>{{ report.displayName || t('detail.untitledTask') }}</strong><span class="muted">{{ timestamp(report.startTime) }} — {{ timestamp(report.endTime) }}</span><span>{{ t('detail.reportLine', { area: area(report.actualCleaningAreaSquareMeter), duration: duration(report.durationSeconds), completion: ratioPercent(report.completionPercentage) }) }}</span></div>
        <div v-if="tabLoading" class="empty"><Loading /> {{ t('common.loading') }}</div>
        <Button v-if="moreReports && !tabLoading" block plain @click="nextReports">{{ t('detail.loadMore') }}</Button>
      </div></Tab>
    </Tabs>
  </div>
</template>

<style scoped>
.offline-banner { display: flex; flex-direction: column; gap: 4px; margin: 0 18px 12px; padding: 12px 14px; border-radius: 10px; background: #fff7e8; border: 1px solid #ffd99a; color: #7a4b00; font-size: 14px; }
.offline-banner .trace { overflow-wrap: anywhere; font-size: 12px; }
.identity { display: flex; align-items: center; gap: 10px; padding: 14px 18px; overflow-wrap: anywhere; }
.action-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
.map-button { width: 100%; border: 0; text-align: left; color: inherit; cursor: pointer; }
.map-image { display: block; width: 100%; margin-top: 12px; object-fit: contain; }
.json { max-height: 160px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; }
select { background: #fff; border: 1px solid #d6e4f4; border-radius: 6px; padding: 6px; }
</style>
