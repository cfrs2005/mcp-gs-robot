<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { RobotStatus } from '@/api/client'
import { fleetRobot, loadFleet } from '@/api/fleet'
import { workStateName } from '@/shared/workStates'
import { shortDateTime } from '@/shared/format'
import RobotImage from '@/components/ui/RobotImage.vue'
import BatteryBar from '@/components/ui/BatteryBar.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import { t } from '@/i18n'

// get_robot_status → { list: RobotStatus[] }; one row per snapshot.
const props = defineProps<{ input: Record<string, unknown>; output: unknown; name?: string }>()
const router = useRouter()
const snapshots = computed<RobotStatus[]>(() => {
  const list = (props.output as { list?: unknown })?.list
  return Array.isArray(list) ? list.filter((s): s is RobotStatus => !!s && typeof (s as RobotStatus).robotSn === 'string') : []
})
// Model and name come from list_robots (the snapshot has neither); failures just drop the photo.
onMounted(() => { loadFleet().catch(() => undefined) })
const info = fleetRobot
const online = (s: RobotStatus) => s.onlineStatus === 'ONLINE'
</script>

<template>
  <div class="status-cards">
    <button v-for="s in snapshots" :key="s.robotSn" type="button" class="robot" @click="router.push(`/robots/${encodeURIComponent(s.robotSn)}`)">
      <RobotImage class="photo" :info="info(s.robotSn)" :alt="s.robotSn" />
      <div class="main">
        <div class="line1"><strong class="sn">{{ s.robotSn }}</strong><StatusPill :tone="online(s) ? 'ok' : 'off'" :label="online(s) ? t('robots.online') : t('robots.offline')" :solid="online(s)" /></div>
        <div v-if="info(s.robotSn)?.displayName && info(s.robotSn)?.displayName !== s.robotSn" class="name">{{ info(s.robotSn)?.displayName }}</div>
        <div class="facts">
          <span>{{ t('detail.workState', { value: workStateName(s) }) }}<template v-if="s.charging"> {{ t('robots.charging') }}</template></span>
          <span>{{ t('robots.map', { value: s.currentMapName || t('common.none') }) }}</span>
          <span v-if="s.taskName">{{ t('detail.currentTask', { value: s.taskName }) }}</span>
        </div>
        <BatteryBar :value="s.batteryPercent" :charging="s.charging" />
        <div v-if="s.observedMsTimestamp" class="observed">{{ t('detail.observedAt', { value: shortDateTime(s.observedMsTimestamp) }) }}</div>
      </div>
    </button>
  </div>
</template>

<style scoped>
.status-cards { display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; }
.robot { display: flex; gap: 12px; width: 100%; padding: 12px; border: 0; border-radius: var(--sd-r-lg); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); text-align: left; color: inherit; cursor: pointer; }
.photo { flex: none; width: 84px; height: 84px; border-radius: var(--sd-r-md); background: var(--sd-primary-softer); }
.main { flex: 1; min-width: 0; display: grid; gap: 6px; align-content: start; }
.line1 { display: flex; align-items: center; gap: 8px; min-width: 0; }
.sn { min-width: 0; font-size: var(--sd-fs-sm); color: var(--sd-ink); overflow-wrap: anywhere; }
.name { font-size: var(--sd-fs-xs); color: var(--sd-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.facts { display: grid; gap: 2px; font-size: var(--sd-fs-sm); color: var(--sd-ink-2); }
.observed { font-size: var(--sd-fs-2xs); color: var(--sd-faint); }
</style>
