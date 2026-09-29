<script setup lang="ts">
// Row of small stat tiles. Only values that exist are passed in; nothing is compared to a made-up baseline.
export type Kpi = { label: string; value: string; unit?: string; hint?: string }
defineProps<{ items: Kpi[] }>()
</script>

<template>
  <div class="kpis" :class="{ quad: items.length >= 4 }" :style="{ '--n': Math.min(items.length, 4) }">
    <div v-for="item in items" :key="item.label" class="kpi">
      <div class="value">{{ item.value }}<small v-if="item.unit">{{ item.unit }}</small></div>
      <div class="label">{{ item.label }}</div>
      <div v-if="item.hint" class="hint">{{ item.hint }}</div>
    </div>
  </div>
</template>

<style scoped>
.kpis { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: var(--sd-s-2); }
@media (max-width: 480px) { .kpis.quad { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.kpi { min-width: 0; padding: 11px 12px; border-radius: var(--sd-r-md); background: var(--sd-surface); box-shadow: inset 0 0 0 1px var(--sd-line); }
.value { font-size: var(--sd-fs-xl); font-weight: 700; color: var(--sd-ink); line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }
.value small { margin-left: 3px; font-size: var(--sd-fs-sm); font-weight: 600; color: var(--sd-ink-2); }
.label { margin-top: 3px; font-size: var(--sd-fs-xs); color: var(--sd-muted); }
.hint { margin-top: 2px; font-size: var(--sd-fs-2xs); color: var(--sd-faint); }
</style>
