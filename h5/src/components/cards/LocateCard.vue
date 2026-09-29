<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getMapCanvas, getMapResources, listChargingPositions, type MapCanvas, type MapInfo, type MapPosition, type RobotStatus } from '@/api/client'
import CardShell from '@/components/ui/CardShell.vue'
import { formatNumber, t } from '@/i18n'
import { timestamp } from '@/shared/format'

// Current localization on the current map PNG. Read-only: nothing here can move the robot.
// Geometry (measured on G102 / "天台", 2026-09-29): PNG size == mapInfo gridWidth × gridHeight; grid
// cells are (world - origin) / resolution, origin bottom-left with y up, so screen top = (H - y) / H.
// angle is degrees, 0 = +x, counter-clockwise (matches the world quaternion yaw), so the arrow turns by -angle.
// Canvas mapInfo wins over the status snapshot's copy when they differ.
const props = defineProps<{ sn: string; status: RobotStatus | null; offline: boolean }>()
const emit = defineEmits<{ refresh: [] }>()

type Point = { key: string; name: string; x: number; y: number; charging: boolean }
const canvas = ref<MapCanvas | null>(null)
const points = ref<Point[]>([])
const loadingMap = ref(false)
const mapError = ref(false)
const imageFailed = ref(false)
const showNames = ref(true)
const refreshing = ref(false)
let loadedFor = ''

const num = (v: unknown): number | null => { const n = typeof v === 'string' ? parseFloat(v) : typeof v === 'number' ? v : NaN; return Number.isFinite(n) ? n : null }
const mapId = computed(() => props.status?.currentMapId || '')

async function loadMap(force = false) {
  const id = mapId.value
  if (!id || (!force && loadedFor === `${props.sn}/${id}`)) return
  loadedFor = `${props.sn}/${id}`
  loadingMap.value = true
  mapError.value = false
  imageFailed.value = false
  const [c, r, ch] = await Promise.allSettled([getMapCanvas(props.sn, id), getMapResources(props.sn, id), listChargingPositions(props.sn, id)])
  if (loadedFor !== `${props.sn}/${id}`) return
  canvas.value = c.status === 'fulfilled' ? c.value : null
  mapError.value = c.status === 'rejected'
  const chargers = ch.status === 'fulfilled' ? ch.value.positions ?? [] : []
  const resources = r.status === 'fulfilled' ? (r.value.maps ?? []).filter(m => !m.mapId || m.mapId === id).flatMap(m => m.positions ?? []) : []
  points.value = mergePoints(resources, chargers)
  showNames.value = points.value.length <= 8
  loadingMap.value = false
}
// One marker per place: a map-resource position at the same cell as a charging position is the same charger.
function mergePoints(resources: MapPosition[], chargers: MapPosition[]): Point[] {
  const out: Point[] = []
  const add = (p: MapPosition, charging: boolean) => {
    const x = num(p.gridX), y = num(p.gridY)
    if (x === null || y === null) return
    const same = out.find(o => Math.abs(o.x - x) <= 1 && Math.abs(o.y - y) <= 1)
    if (same) { same.charging ||= charging; return }
    out.push({ key: p.mapResourceId || `${x},${y}`, name: p.positionName || p.mapResourceName || '', x, y, charging })
  }
  chargers.forEach(p => add(p, true))
  resources.forEach(p => add(p, false))
  return out
}
watch(() => [props.sn, mapId.value] as const, () => void loadMap(), { immediate: true })

const info = computed<MapInfo | undefined>(() => canvas.value?.mapInfo ?? props.status?.position?.mapInfo)
const infoDiffers = computed(() => {
  const a = canvas.value?.mapInfo, b = props.status?.position?.mapInfo
  if (!a || !b) return false
  return (['gridWidth', 'gridHeight', 'originX', 'originY', 'resolution'] as const).some(k => a[k] !== b[k])
})
const W = computed(() => num(info.value?.gridWidth) ?? 0)
const H = computed(() => num(info.value?.gridHeight) ?? 0)
const grid = computed(() => {
  const g = props.status?.position?.gridPosition
  const x = num(g?.x), y = num(g?.y)
  return x === null || y === null ? null : { x, y }
})
const angle = computed(() => num(props.status?.position?.angle))
const inside = computed(() => !!grid.value && W.value > 0 && H.value > 0 && grid.value.x >= 0 && grid.value.x <= W.value && grid.value.y >= 0 && grid.value.y <= H.value)
const pct = (x: number, y: number) => ({ left: `${(x / W.value) * 100}%`, top: `${((H.value - y) / H.value) * 100}%` })
const imageUrl = computed(() => canvas.value?.mapPng?.exist !== false ? canvas.value?.mapPng?.downloadUri || '' : '')

type Empty = 'offline' | 'noStatus' | 'noMap' | 'noPosition' | 'outside' | null
const empty = computed<Empty>(() => {
  if (props.offline) return 'offline'
  if (!props.status) return 'noStatus'
  if (!mapId.value) return 'noMap'
  if (!grid.value) return 'noPosition'
  if (W.value > 0 && !inside.value) return 'outside'
  return null
})
const EMPTY_TEXT = { offline: 'locate.offline', noStatus: 'locate.noStatus', noMap: 'locate.noMap', noPosition: 'locate.noPosition', outside: 'locate.outside' } as const

// Wide maps (like 1449 × 469) get a minimum stage width and scroll inside the card, centred on the robot.
const viewport = ref<HTMLElement | null>(null)
const minWidth = computed(() => (W.value && H.value && W.value / H.value > 2 ? 640 : 0))
async function centre() {
  await nextTick()
  const el = viewport.value
  if (!el || !grid.value || !W.value) return
  el.scrollLeft = (grid.value.x / W.value) * el.scrollWidth - el.clientWidth / 2
}
watch(() => [grid.value?.x, W.value, minWidth.value], () => void centre())
// Marker positions are percentages of the stage, so resizing never moves them; only re-centre the scroll.
const onResize = () => void centre()
onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => window.removeEventListener('resize', onResize))

async function refresh() {
  refreshing.value = true
  emit('refresh')
  if (imageFailed.value || mapError.value) await loadMap(true)
  setTimeout(() => { refreshing.value = false }, 600)
}
const fmt = (v: number) => formatNumber(v, { maximumFractionDigits: 1 })
</script>

<template>
  <CardShell :title="t('locate.title')" :subtitle="status?.currentMapName || undefined" icon="map">
    <template #action><button type="button" class="link-btn" :disabled="refreshing" @click="refresh">{{ t('detail.refresh') }}</button></template>
    <div v-if="empty" class="empty-state">{{ t(EMPTY_TEXT[empty]) }}</div>
    <template v-else>
      <div v-if="loadingMap && !canvas" class="empty-state">{{ t('common.loading') }}</div>
      <div v-else-if="mapError || !imageUrl || imageFailed" class="empty-state">{{ t('locate.imageFailed') }}</div>
      <div v-else ref="viewport" class="viewport">
        <div class="stage" :style="{ aspectRatio: `${W} / ${H}`, minWidth: minWidth ? `${minWidth}px` : undefined }">
          <img :src="imageUrl" :alt="status?.currentMapName || t('cards.mapAlt')" referrerpolicy="no-referrer" @error="imageFailed = true" @load="centre">
          <div v-for="p in points" :key="p.key" class="point" :class="{ charging: p.charging }" :style="pct(p.x, p.y)" :title="p.name">
            <svg v-if="p.charging" viewBox="0 0 16 16" aria-hidden="true"><rect x="1" y="1" width="14" height="14" rx="4" /><path d="M9 3.5L5.5 9H8l-1 3.5L10.5 7H8z" /></svg>
            <svg v-else viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.5a4.5 4.5 0 0 0-4.5 4.5c0 3.4 4.5 8.5 4.5 8.5s4.5-5.1 4.5-8.5A4.5 4.5 0 0 0 8 1.5z" /><circle cx="8" cy="6" r="1.7" /></svg>
            <span v-if="showNames && p.name" class="label">{{ p.name }}</span>
          </div>
          <div v-if="grid" class="robot" :style="pct(grid.x, grid.y)" :aria-label="t('locate.robot')">
            <span class="pulse" />
            <span v-if="angle !== null" class="heading" :style="{ transform: `rotate(${-angle}deg)` }"><i /></span>
            <span class="dot" />
          </div>
        </div>
      </div>
      <div class="legend">
        <span><i class="lg-robot" />{{ t('locate.robot') }}</span>
        <span v-if="points.some(p => p.charging)"><i class="lg-charger" />{{ t('locate.charger') }}</span>
        <span v-if="points.some(p => !p.charging)"><i class="lg-point" />{{ t('locate.point') }}</span>
        <label v-if="points.length" class="names"><input v-model="showNames" type="checkbox">{{ t('locate.showNames') }}</label>
      </div>
      <dl class="facts">
        <dt>{{ t('locate.grid') }}</dt><dd>({{ fmt(grid!.x) }}, {{ fmt(grid!.y) }})</dd>
        <dt>{{ t('locate.heading') }}</dt><dd>{{ angle === null ? '—' : `${fmt(angle)}°` }}</dd>
        <dt>{{ t('locate.map') }}</dt><dd>{{ status?.currentMapName || '—' }}<template v-if="W"> · {{ fmt(W) }} × {{ fmt(H) }}</template></dd>
        <dt>{{ t('locate.time') }}</dt><dd>{{ timestamp(status?.observedMsTimestamp) }}</dd>
      </dl>
      <p v-if="infoDiffers" class="note">{{ t('locate.mapInfoDiff') }}</p>
    </template>
  </CardShell>
</template>

<style scoped>
.link-btn { height: 30px; padding: 0 12px; border: 1px solid var(--sd-primary-line); border-radius: var(--sd-r-pill); background: var(--sd-surface); color: var(--sd-primary); font-size: var(--sd-fs-xs); font-weight: 600; cursor: pointer; }
.link-btn:disabled { opacity: .5; }
.empty-state { padding: 22px 12px; border-radius: var(--sd-r-md); background: var(--sd-surface-2); color: var(--sd-muted); font-size: var(--sd-fs-sm); text-align: center; }
.viewport { overflow-x: auto; border-radius: var(--sd-r-md); box-shadow: inset 0 0 0 1px var(--sd-line); -webkit-overflow-scrolling: touch; }
.stage { position: relative; width: 100%; }
.stage img { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.point { position: absolute; transform: translate(-50%, -50%); display: flex; align-items: center; gap: 3px; pointer-events: none; }
.point svg { width: 14px; height: 14px; flex: none; fill: var(--sd-primary); stroke: var(--sd-on-primary); stroke-width: 1.2; }
.point.charging svg { width: 16px; height: 16px; fill: var(--sd-success); }
.point.charging svg path { fill: var(--sd-on-primary); stroke: none; }
.point svg circle { fill: var(--sd-on-primary); stroke: none; }
.label { position: absolute; left: 100%; margin-left: 3px; padding: 1px 5px; border-radius: var(--sd-r-xs); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); color: var(--sd-ink); font-size: var(--sd-fs-2xs); white-space: nowrap; }
.robot { position: absolute; width: 0; height: 0; }
.dot { position: absolute; left: -6px; top: -6px; width: 12px; height: 12px; border-radius: 50%; background: var(--sd-danger); box-shadow: 0 0 0 2px var(--sd-on-primary); }
.pulse { position: absolute; left: -6px; top: -6px; width: 12px; height: 12px; border-radius: 50%; background: var(--sd-danger); animation: pulse 1.6s ease-out infinite; }
@keyframes pulse { 0% { transform: scale(1); opacity: .55; } 100% { transform: scale(3.4); opacity: 0; } }
.heading { position: absolute; left: 0; top: 0; width: 0; height: 0; transform-origin: 0 0; }
.heading i { position: absolute; left: 7px; top: -6px; width: 0; height: 0; border-top: 6px solid transparent; border-bottom: 6px solid transparent; border-left: 11px solid var(--sd-danger); }
.legend { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; font-size: var(--sd-fs-xs); color: var(--sd-ink-2); }
.legend span { display: inline-flex; align-items: center; gap: 5px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.lg-robot { background: var(--sd-danger); }
.lg-charger { background: var(--sd-success); border-radius: 3px !important; }
.lg-point { background: var(--sd-primary); }
.names { display: inline-flex; align-items: center; gap: 5px; margin-left: auto; cursor: pointer; }
.facts { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 5px 14px; margin: 0; font-size: var(--sd-fs-sm); }
.facts dt { color: var(--sd-muted); }
.facts dd { margin: 0; color: var(--sd-ink); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.note { margin: 0; font-size: var(--sd-fs-xs); color: var(--sd-warning); }
</style>
