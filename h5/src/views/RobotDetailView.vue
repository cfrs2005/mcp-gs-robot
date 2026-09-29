<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Tabs, Tab, Tag, Progress, Loading, showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import {
  getRobotStatus, getCapabilities, listMaps, getMapCanvas, listTaskDefinitions, listReports,
  startTask, pauseTask, resumeTask, stopTask, navigateHome, pageItems,
  type RobotStatus, type RobotMap, type MapCanvas, type TaskDefinition, type TaskReport,
} from '@/api/client'
import { workStateName } from '@/workStates'

const route = useRoute()
const router = useRouter()
const sn = String(route.params.sn)
const tab = ref('overview')
const status = ref<RobotStatus | null>(null)
const goHome = () => {
  const mapId = status.value?.currentMapId
  if (!mapId) { showFailToast('机器人当前未定位到地图，无法回充'); return }
  return action('回充', () => navigateHome(sn, mapId))
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

function fail(e: unknown) { showFailToast(e instanceof Error ? e.message : '请求失败') }
async function refreshStatus() {
  try { status.value = await getRobotStatus(sn) } catch (e) { fail(e) }
}
async function loadTab(name: string) {
  tabLoading.value = true
  try {
    if (name === 'maps') maps.value = pageItems(await listMaps(sn))
    if (name === 'tasks') definitions.value = pageItems(await listTaskDefinitions(sn))
    if (name === 'reports') { reportsPage.value = 1; reports.value = []; await loadReports() }
  } catch (e) { fail(e) }
  finally { tabLoading.value = false }
}
async function loadReports() {
  const data = await listReports(sn, reportsPage.value)
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
  try { canvas.value = await getMapCanvas(sn, mapId) } catch (e) { fail(e) }
  finally { tabLoading.value = false }
}
async function action(label: string, run: () => Promise<unknown>) {
  if (busy.value) return
  try { await showConfirmDialog({ title: `确认${label}`, message: `将对机器人 ${sn} 执行「${label}」，是否继续？` }) }
  catch { return }
  busy.value = true
  try { await run(); showSuccessToast(`${label}指令已下发`); await refreshStatus() }
  catch (e) { fail(e) }
  finally { busy.value = false }
}
function start(definition: TaskDefinition) {
  void action(`启动任务「${definition.taskName}」（${loopCount.value} 次）`, () => startTask(sn, definition.fusionTaskId, loopCount.value))
}
function timestamp(value?: number): string {
  if (!value) return '—'
  const date = new Date(value < 1e11 ? value * 1000 : value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('zh-CN', { hour12: false })
}
function duration(seconds?: number): string { return seconds === undefined ? '—' : `${Math.round(seconds / 60)} 分钟` }
function percent(value?: number): string { return value === undefined ? '—' : `${Math.round(value * 10) / 10}%` }
watch(tab, value => { if (value !== 'overview') void loadTab(value) })
onMounted(async () => {
  loading.value = true
  await refreshStatus()
  try { capabilities.value = await getCapabilities(sn) } catch (e) { fail(e) }
  loading.value = false
})
</script>

<template>
  <div class="page">
    <header class="page-header"><div class="row"><Button icon="arrow-left" size="small" plain @click="router.push('/robots')" />机器人详情</div><Button size="small" plain @click="refreshStatus">刷新</Button></header>
    <div class="identity"><strong>{{ sn }}</strong><Tag :type="status?.onlineStatus === 'ONLINE' ? 'success' : 'default'">{{ status?.onlineStatus === 'ONLINE' ? '在线' : '离线' }}</Tag></div>
    <Tabs v-model:active="tab" sticky>
      <Tab title="概览" name="overview">
        <div class="page-body">
          <div v-if="loading" class="empty"><Loading /> 加载中…</div>
          <div v-else-if="status" class="panel stack">
            <div>工作状态：{{ workStateName(status) }}</div>
            <div>当前地图：{{ status.currentMapName || '暂无' }}</div>
            <div>当前任务：{{ status.taskName || '暂无' }}</div>
            <div>电量：{{ status.batteryPercent ?? '—' }}% <span v-if="status.charging">（充电中）</span><Progress :percentage="status.batteryPercent ?? 0" :show-pivot="false" /></div>
            <div class="muted">状态时间：{{ timestamp(status.observedMsTimestamp) }}</div>
          </div>
          <div v-if="capabilities !== null" class="panel"><strong>机器人能力</strong><pre class="json">{{ JSON.stringify(capabilities, null, 2) }}</pre></div>
          <div class="panel"><strong>快捷操作</strong><p class="muted">启动任务请先在「任务」页选择任务定义</p><div class="action-grid">
            <Button size="small" type="primary" :disabled="busy" @click="tab = 'tasks'">选择任务并启动</Button>
            <Button size="small" :disabled="busy" @click="action('暂停任务', () => pauseTask(sn))">暂停</Button>
            <Button size="small" :disabled="busy" @click="action('继续任务', () => resumeTask(sn))">继续</Button>
            <Button size="small" type="danger" plain :disabled="busy" @click="action('停止任务', () => stopTask(sn))">停止</Button>
            <Button size="small" :disabled="busy" @click="goHome()">回充</Button>
          </div></div>
        </div>
      </Tab>
      <Tab title="地图" name="maps"><div class="page-body">
        <div v-if="!maps.length && !tabLoading" class="empty">暂无地图</div>
        <button v-for="map in maps" :key="map.mapId" class="panel map-button" type="button" @click="selectMap(map.mapId)">{{ map.displayName || map.mapId }}</button>
        <div v-if="tabLoading" class="empty"><Loading /> 加载中…</div>
        <div v-if="canvas" class="panel"><strong>地图画布</strong><img v-if="canvas.mapPng?.exist && canvas.mapPng.downloadUri" class="map-image" :src="canvas.mapPng.downloadUri" alt="地图画布" /><p v-else class="muted">暂无地图图片</p><p v-if="canvas.mapInfo" class="muted">尺寸 {{ canvas.mapInfo.gridWidth }} × {{ canvas.mapInfo.gridHeight }} · 分辨率 {{ canvas.mapInfo.resolution }} m/格 · 原点 ({{ canvas.mapInfo.originX }}, {{ canvas.mapInfo.originY }})</p></div>
      </div></Tab>
      <Tab title="任务" name="tasks"><div class="page-body">
        <div class="panel row"><span>循环次数</span><select v-model.number="loopCount" aria-label="循环次数"><option v-for="n in [1, 2, 3]" :key="n" :value="n">{{ n }} 次</option></select></div>
        <div v-if="!definitions.length && !tabLoading" class="empty">暂无任务定义</div>
        <div v-for="definition in definitions" :key="definition.fusionTaskId" class="panel row between"><div><strong>{{ definition.taskName || '未命名任务' }}</strong><div class="muted">{{ definition.fusionTaskId }}</div></div><Button size="small" type="primary" :disabled="busy" @click="start(definition)">启动</Button></div>
        <div v-if="tabLoading" class="empty"><Loading /> 加载中…</div>
      </div></Tab>
      <Tab title="报告" name="reports"><div class="page-body">
        <div v-if="!reports.length && !tabLoading" class="empty">暂无报告</div>
        <div v-for="(report, index) in reports" :key="report.id || index" class="panel stack"><strong>{{ report.displayName || '未命名任务' }}</strong><span class="muted">{{ timestamp(report.startTime) }} — {{ timestamp(report.endTime) }}</span><span>面积 {{ report.actualCleaningAreaSquareMeter ?? '—' }} m² · 用时 {{ duration(report.durationSeconds) }} · 完成 {{ percent(report.completionPercentage) }}</span></div>
        <div v-if="tabLoading" class="empty"><Loading /> 加载中…</div>
        <Button v-if="moreReports && !tabLoading" block plain @click="nextReports">加载更多</Button>
      </div></Tab>
    </Tabs>
  </div>
</template>

<style scoped>
.identity { display: flex; align-items: center; gap: 10px; padding: 14px 18px; overflow-wrap: anywhere; }
.action-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
.map-button { width: 100%; border: 0; text-align: left; color: inherit; cursor: pointer; }
.map-image { display: block; width: 100%; margin-top: 12px; object-fit: contain; }
.json { max-height: 160px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; }
select { background: #fff; border: 1px solid #d6e4f4; border-radius: 6px; padding: 6px; }
</style>
