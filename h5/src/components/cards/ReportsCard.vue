<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { TaskReport } from '@/api/client'
import { areaByDay, newest, summarize } from '@/shared/reports'
import { area, minutes, ratioPercent, shortDateTime, toDate } from '@/shared/format'
import CardShell from '@/components/ui/CardShell.vue'
import KpiGrid, { type Kpi } from '@/components/ui/KpiGrid.vue'
import BarChart from '@/components/ui/BarChart.vue'
import { formatDateTime, formatNumber, t } from '@/i18n'

// list_task_reports → { robotTaskReports: TaskReport[], count }. KPIs cover only the returned page.
const props = defineProps<{ input: Record<string, unknown>; output: unknown; name?: string }>()
const router = useRouter()
const reports = computed<TaskReport[]>(() => {
  const list = (props.output as { robotTaskReports?: unknown })?.robotTaskReports
  return Array.isArray(list) ? list.filter((r): r is TaskReport => !!r && typeof r === 'object') : []
})
const total = computed(() => {
  const count = (props.output as { count?: unknown })?.count
  return typeof count === 'number' ? count : null
})
const sn = computed(() => typeof props.input.robot_sn === 'string' ? props.input.robot_sn : reports.value.find(r => r.robotSerialNumber)?.robotSerialNumber)
const summary = computed(() => summarize(reports.value))
const kpis = computed<Kpi[]>(() => {
  const s = summary.value
  const items: Kpi[] = [{ label: t('cards.tasks'), value: formatNumber(s.count), hint: total.value !== null && total.value > s.count ? t('cards.ofTotal', { total: formatNumber(total.value) }) : undefined }]
  if (s.totalArea !== null) items.push({ label: t('cards.totalArea'), value: area(s.totalArea, 0), unit: 'm²' })
  if (s.avgDuration !== null) items.push({ label: t('cards.avgDuration'), value: minutes(s.avgDuration) })
  if (s.avgCompletion !== null) items.push({ label: t('cards.avgCompletion'), value: ratioPercent(s.avgCompletion) })
  return items
})
const days = computed(() => areaByDay(reports.value))
const recent = computed(() => newest(reports.value, 3))
const range = computed(() => {
  const times = reports.value.flatMap(r => [toDate(r.startTime), toDate(r.endTime)]).filter((d): d is Date => d !== null).map(d => d.getTime())
  if (!times.length) return ''
  const f = (ms: number) => formatDateTime(new Date(ms), { month: 'short', day: 'numeric' })
  const [a, b] = [f(Math.min(...times)), f(Math.max(...times))]
  return a === b ? a : `${a} – ${b}`
})
const subtitle = computed(() => [sn.value, range.value].filter(Boolean).join(' · '))
const open = () => sn.value && router.push({ path: `/robots/${encodeURIComponent(sn.value)}`, query: { tab: 'reports' } })
</script>

<template>
  <CardShell :title="t('cards.reportsTitle')" :subtitle="subtitle" icon="chart">
    <template v-if="sn" #action><button type="button" class="link-btn" @click="open">{{ t('cards.viewReports') }} ›</button></template>
    <KpiGrid :items="kpis" />
    <div v-if="days.length" class="chart-box">
      <div class="chart-title">{{ t('cards.areaTrend') }}</div>
      <BarChart :points="days" unit="m²" :title="t('cards.areaTrend')" />
    </div>
    <ul class="recent">
      <li v-for="(r, i) in recent" :key="r.id || i">
        <span class="dot" aria-hidden="true" />
        <div class="r-main"><strong>{{ r.displayName || t('detail.untitledTask') }}</strong><span>{{ shortDateTime(r.startTime) }}<template v-if="r.cleaningMode"> · {{ r.cleaningMode }}</template></span></div>
        <div class="r-nums"><strong>{{ area(r.actualCleaningAreaSquareMeter, 1) }} m²</strong><span>{{ minutes(r.durationSeconds) }} · {{ ratioPercent(r.completionPercentage) }}</span></div>
      </li>
    </ul>
  </CardShell>
</template>

<style scoped>
.link-btn { height: 30px; padding: 0 12px; border: 1px solid var(--sd-primary-line); border-radius: var(--sd-r-pill); background: var(--sd-surface); color: var(--sd-primary); font-size: var(--sd-fs-xs); font-weight: 600; cursor: pointer; white-space: nowrap; }
.chart-box { padding: 12px 12px 8px; border-radius: var(--sd-r-md); box-shadow: inset 0 0 0 1px var(--sd-line); }
.chart-title { margin-bottom: 4px; font-size: var(--sd-fs-sm); font-weight: 650; color: var(--sd-ink); }
.recent { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: minmax(0, 1fr); gap: 2px; }
.recent li { display: flex; align-items: center; gap: 10px; padding: 8px 4px; border-top: 1px solid var(--sd-line); }
.recent li:first-child { border-top: 0; }
.dot { flex: none; width: 8px; height: 8px; border-radius: 50%; background: var(--sd-primary-line); }
.r-main, .r-nums { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.r-main { flex: 1; }
.r-nums { flex: none; text-align: right; }
.recent strong { font-size: var(--sd-fs-sm); color: var(--sd-ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recent span { font-size: var(--sd-fs-xs); color: var(--sd-muted); white-space: nowrap; }
</style>
