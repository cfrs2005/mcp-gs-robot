<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PullRefresh, Tag, Progress, Loading, showFailToast } from 'vant'
import { ApiError, batchRobotStatus, listRobots, messageForCode, pageItems, robotErrorMessage, type Robot, type RobotStatus } from '@/api/client'
import { workStateName } from '@/workStates'
import { t } from '@/i18n'

type Card = Robot & Partial<RobotStatus> & { online: boolean }

const router = useRouter()
const robots = ref<Card[]>([])
const refreshing = ref(false)
const loading = ref(false)
const error = ref('')
const onlineCount = computed(() => robots.value.filter(reachable).length)

// Live status is only queried for online robots; offline ones are skipped (upstream rejects the whole batch with 230003).
// If a batch still fails (state just changed), only that batch is greyed out, with no global toast.
async function liveStatuses(sns: string[]): Promise<Map<string, Partial<RobotStatus>>> {
  const chunks = Array.from({ length: Math.ceil(sns.length / 100) }, (_, i) => sns.slice(i * 100, i * 100 + 100))
  const settled = await Promise.allSettled(chunks.map(chunk => batchRobotStatus(chunk)))
  const bySn = new Map<string, Partial<RobotStatus>>()
  settled.forEach((result, i) => {
    if (result.status === 'fulfilled') pageItems(result.value).forEach(item => bySn.set(item.robotSn, item))
    else chunks[i].forEach(sn => bySn.set(sn, { reachable: false, error: { code: result.reason instanceof ApiError ? result.reason.code : undefined, message: robotErrorMessage(result.reason) } }))
  })
  return bySn
}
function reachable(robot: Card): boolean {
  return robot.online && robot.reachable !== false && robot.onlineStatus !== 'OFFLINE'
}
// Three card kinds: online (live status) / offline (flagged by list or snapshot) / unreachable (upstream 230003 on query).
function tagText(robot: Card): string {
  return reachable(robot) ? t('robots.online') : robot.reachable === false ? t('robots.unreachable') : t('robots.offline')
}
function statusText(robot: Card): string {
  if (reachable(robot)) return workStateName(robot)
  // Localize by error.code; the server's message is only a fallback for codes the UI does not know.
  if (robot.reachable === false) return t('robots.statusUnreachable', { message: messageForCode(robot.error?.code ?? 230003, robot.error?.message) })
  return t('robots.statusOffline')
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    const listed = pageItems(await listRobots())
      .map(item => ({ ...item, online: item.online === true }))
      .sort((a, b) => Number(b.online) - Number(a.online))
    robots.value = listed
    const bySn = await liveStatuses(listed.filter(item => item.online).map(item => item.robotSn))
    const merged: Card[] = listed.map(item => ({ ...item, ...bySn.get(item.robotSn) }))
    robots.value = merged.sort((a, b) => Number(reachable(b)) - Number(reachable(a)))
  } catch (e) {
    error.value = robotErrorMessage(e) || t('robots.loadFailed')
    showFailToast(error.value)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="page">
    <header class="page-header">{{ t('robots.title') }} <span class="muted">{{ t('robots.summary', { online: onlineCount, total: robots.length }) }}</span></header>
    <PullRefresh v-model="refreshing" @refresh="load">
      <div class="page-body">
        <div v-if="loading && !refreshing" class="empty"><Loading /> {{ t('common.loading') }}</div>
        <div v-else-if="!robots.length" class="empty">{{ error || t('robots.empty') }}</div>
        <button v-for="robot in robots" :key="robot.robotSn" class="panel robot-card" :class="{ inactive: !reachable(robot) }" type="button" @click="router.push(`/robots/${encodeURIComponent(robot.robotSn)}`)">
          <div class="row between"><strong>{{ robot.robotSn }}</strong><Tag :type="reachable(robot) ? 'success' : 'default'">{{ tagText(robot) }}</Tag></div>
          <p>{{ t('robots.status', { value: statusText(robot) }) }} <span v-if="reachable(robot) && robot.charging">{{ t('robots.charging') }}</span></p>
          <p>{{ t('robots.map', { value: reachable(robot) ? robot.currentMapName || t('common.none') : '—' }) }}</p>
          <div class="row"><span class="muted">{{ t('robots.battery') }}</span><Progress class="battery" :percentage="reachable(robot) ? robot.batteryPercent ?? 0 : 0" :show-pivot="false" /><span>{{ reachable(robot) ? robot.batteryPercent ?? '—' : '—' }}%</span></div>
        </button>
      </div>
    </PullRefresh>
  </div>
</template>

<style scoped>
.robot-card { width: 100%; border: 0; text-align: left; color: inherit; cursor: pointer; }
.robot-card p { margin: 10px 0; font-size: 14px; }
.battery { flex: 1; }
.robot-card.inactive { background: #f4f6f9; color: #8a94a3; box-shadow: none; }
.robot-card.inactive strong { color: #5f6b7a; }
</style>
