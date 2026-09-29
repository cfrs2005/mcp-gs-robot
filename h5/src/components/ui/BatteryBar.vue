<script setup lang="ts">
import { computed } from 'vue'

// Battery 0–100 (upstream batteryPercent). Unknown shows an empty track and "—".
const props = defineProps<{ value?: number | null; charging?: boolean; compact?: boolean }>()
const known = computed(() => typeof props.value === 'number' && Number.isFinite(props.value))
const pct = computed(() => known.value ? Math.max(0, Math.min(100, props.value as number)) : 0)
const level = computed(() => !known.value ? 'none' : pct.value <= 20 ? 'low' : pct.value <= 40 ? 'mid' : 'ok')
</script>

<template>
  <div class="battery" :class="[level, { compact }]">
    <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="16" height="10" rx="2.5" /><path d="M21 10.5v3" />
      <path v-if="charging" d="M12 8.5l-2.6 4h3l-1.4 3.2" class="bolt" /></svg>
    <div class="track"><div class="fill" :style="{ width: `${pct}%` }" /></div>
    <span class="num">{{ known ? `${Math.round(pct)}%` : '—' }}</span>
  </div>
</template>

<style scoped>
.battery { display: flex; align-items: center; gap: 7px; min-width: 0; }
.icon { width: 18px; height: 18px; flex: none; fill: none; stroke: var(--sd-muted); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.icon .bolt { stroke: var(--sd-warning); }
.track { flex: 1; height: 6px; border-radius: var(--sd-r-pill); background: var(--sd-line); overflow: hidden; min-width: 28px; }
.fill { height: 100%; border-radius: inherit; background: var(--sd-success); transition: width .3s; }
.mid .fill { background: var(--sd-primary); }
.low .fill { background: var(--sd-danger); }
.num { flex: none; min-width: 34px; text-align: right; font-size: var(--sd-fs-sm); font-weight: 600; color: var(--sd-ink); font-variant-numeric: tabular-nums; }
.compact .track { display: none; }
.compact .num { min-width: 0; }
</style>
