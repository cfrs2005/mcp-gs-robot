<script setup lang="ts">
import { computed, ref } from 'vue'
import { formatNumber } from '@/i18n'

// Hand-drawn single-series bar chart (no chart dependency): one hue, recessive grid, y ticks, the latest
// bar highlighted and directly labeled; hovering / tapping a bar labels that bar instead.
export type BarPoint = { key: string; label: string; value: number }
const props = defineProps<{ points: BarPoint[]; unit: string; title: string }>()

const W = 320, H = 156, L = 42, R = 8, T = 22, B = 26
const plotW = W - L - R, plotH = H - T - B
function niceStep(raw: number): number {
  if (raw <= 0) return 1
  const exp = 10 ** Math.floor(Math.log10(raw))
  const f = raw / exp
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * exp
}
const scale = computed(() => {
  const max = Math.max(0, ...props.points.map(p => p.value))
  const step = niceStep(max / 4)
  const top = Math.max(step, Math.ceil(max / step) * step)
  const ticks = Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step)
  return { top, ticks }
})
const y = (v: number) => T + plotH - (v / scale.value.top) * plotH
const slot = computed(() => plotW / Math.max(props.points.length, 1))
const barW = computed(() => Math.min(26, slot.value * 0.58))
const labelEvery = computed(() => Math.ceil(props.points.length / 7))
const active = ref<number | null>(null)
const shown = computed(() => active.value ?? props.points.length - 1)
const fmt = (v: number) => formatNumber(v, { maximumFractionDigits: v >= 100 ? 0 : 1 })
function barPath(i: number, v: number): string {
  const x = L + slot.value * i + (slot.value - barW.value) / 2
  const y0 = T + plotH, y1 = Math.min(y(v), y0 - 1)
  const r = Math.min(4, barW.value / 2, y0 - y1)
  return `M${x} ${y0}V${y1 + r}Q${x} ${y1} ${x + r} ${y1}H${x + barW.value - r}Q${x + barW.value} ${y1} ${x + barW.value} ${y1 + r}V${y0}Z`
}
const cx = (i: number) => L + slot.value * i + slot.value / 2
const summary = computed(() => `${props.title}: ${props.points.map(p => `${p.label} ${fmt(p.value)} ${props.unit}`).join(', ')}`)
</script>

<template>
  <svg class="chart" :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="summary" @pointerleave="active = null">
    <text :x="L - 8" :y="T - 10" class="unit" text-anchor="end">{{ unit }}</text>
    <g v-for="tick in scale.ticks" :key="tick">
      <line :x1="L" :x2="W - R" :y1="y(tick)" :y2="y(tick)" class="grid" :class="{ base: tick === 0 }" />
      <text :x="L - 8" :y="y(tick) + 3.5" class="tick" text-anchor="end">{{ fmt(tick) }}</text>
    </g>
    <g v-for="(point, i) in points" :key="point.key">
      <path :d="barPath(i, point.value)" class="bar" :class="{ on: i === shown }" />
      <rect :x="L + slot * i" :y="T" :width="slot" :height="plotH" class="hit" @pointerenter="active = i" @click="active = i"><title>{{ point.label }} · {{ fmt(point.value) }} {{ unit }}</title></rect>
      <text v-if="i % labelEvery === 0 || i === points.length - 1" :x="cx(i)" :y="H - 8" class="tick" :class="{ strong: i === shown }" text-anchor="middle">{{ point.label }}</text>
    </g>
    <text v-if="points.length" :x="Math.min(Math.max(cx(shown), L + 24), W - R - 24)" :y="y(points[shown].value) - 6" class="value" text-anchor="middle">{{ fmt(points[shown].value) }}</text>
  </svg>
</template>

<style scoped>
.chart { display: block; width: 100%; height: auto; overflow: visible; font-family: var(--sd-font); }
.grid { stroke: var(--sd-chart-grid); stroke-width: 1; }
.grid.base { stroke: var(--sd-line-strong); }
.tick { font-size: 10px; fill: var(--sd-muted); font-variant-numeric: tabular-nums; }
.tick.strong { fill: var(--sd-ink); font-weight: 600; }
.unit { font-size: 10px; fill: var(--sd-muted); }
.bar { fill: var(--sd-chart-bar); transition: fill .15s; }
.bar.on { fill: var(--sd-primary); }
.hit { fill: transparent; cursor: pointer; }
.value { font-size: 11px; font-weight: 700; fill: var(--sd-ink); font-variant-numeric: tabular-nums; }
</style>
