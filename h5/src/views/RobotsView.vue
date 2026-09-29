<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PullRefresh, Tag, Progress, Loading, showFailToast } from 'vant'
import { batchRobotStatus, listRobots, pageItems, type RobotStatus } from '@/api/client'
import { workStateName } from '@/workStates'

const router = useRouter()
const robots = ref<RobotStatus[]>([])
const refreshing = ref(false)
const loading = ref(false)
const error = ref('')
async function load() {
  loading.value = true
  error.value = ''
  try {
    const listed = pageItems(await listRobots())
    const sns = listed.map(item => item.robotSn).filter(Boolean)
    const statuses = (await Promise.all(Array.from({ length: Math.ceil(sns.length / 100) }, (_, i) => batchRobotStatus(sns.slice(i * 100, i * 100 + 100))))).flatMap(pageItems)
    const bySn = new Map(statuses.map(item => [item.robotSn, item]))
    robots.value = listed.map(item => ({ ...item, ...bySn.get(item.robotSn) }))
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载机器人失败'
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
    <header class="page-header">机器人 <span class="muted">{{ robots.length }} 台</span></header>
    <PullRefresh v-model="refreshing" @refresh="load">
      <div class="page-body">
        <div v-if="loading && !refreshing" class="empty"><Loading /> 加载中…</div>
        <div v-else-if="!robots.length" class="empty">{{ error || '暂无机器人，下拉刷新' }}</div>
        <button v-for="robot in robots" :key="robot.robotSn" class="panel robot-card" type="button" @click="router.push(`/robots/${encodeURIComponent(robot.robotSn)}`)">
          <div class="row between"><strong>{{ robot.robotSn }}</strong><Tag :type="robot.onlineStatus === 'ONLINE' ? 'success' : 'default'">{{ robot.onlineStatus === 'ONLINE' ? '在线' : '离线' }}</Tag></div>
          <p>状态：{{ workStateName(robot) }} <span v-if="robot.charging">· 充电中</span></p>
          <p>地图：{{ robot.currentMapName || '暂无' }}</p>
          <div class="row"><span class="muted">电量</span><Progress class="battery" :percentage="robot.batteryPercent ?? 0" :show-pivot="false" /><span>{{ robot.batteryPercent ?? '—' }}%</span></div>
        </button>
      </div>
    </PullRefresh>
  </div>
</template>

<style scoped>
.robot-card { width: 100%; border: 0; text-align: left; color: inherit; cursor: pointer; }
.robot-card p { margin: 10px 0; font-size: 14px; }
.battery { flex: 1; }
</style>
