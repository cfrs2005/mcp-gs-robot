<script setup lang="ts">
// Common chrome for result cards: icon tile, title, subtitle, optional header action.
defineProps<{ title: string; subtitle?: string; icon?: 'chart' | 'robot' | 'map' | 'report' }>()
</script>

<template>
  <section class="card-shell">
    <header class="head">
      <span v-if="icon" class="icon" aria-hidden="true">
        <svg v-if="icon === 'chart'" viewBox="0 0 24 24"><path d="M6 19V11M12 19V5M18 19v-6" /></svg>
        <svg v-else-if="icon === 'robot'" viewBox="0 0 24 24"><rect x="4" y="8" width="16" height="11" rx="3.5" /><path d="M12 4v4M9 13.5h.01M15 13.5h.01" /></svg>
        <svg v-else-if="icon === 'map'" viewBox="0 0 24 24"><path d="M3 6.5l6-2.5 6 2.5 6-2.5v13.5l-6 2.5-6-2.5-6 2.5z" /><path d="M9 4v13.5M15 6.5V20" /></svg>
        <svg v-else viewBox="0 0 24 24"><path d="M7 3.5h7l4 4V20a.5.5 0 0 1-.5.5h-10.5a.5.5 0 0 1-.5-.5V4a.5.5 0 0 1 .5-.5z" /><path d="M9 12h6M9 16h4" /></svg>
      </span>
      <div class="titles"><strong>{{ title }}</strong><span v-if="subtitle">{{ subtitle }}</span></div>
      <div v-if="$slots.action" class="action"><slot name="action" /></div>
    </header>
    <div class="body"><slot /></div>
  </section>
</template>

<style scoped>
.card-shell { padding: 14px; border-radius: var(--sd-r-lg); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); }
.head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; min-width: 0; }
.icon { flex: none; display: grid; place-items: center; width: 36px; height: 36px; border-radius: var(--sd-r-sm); background: var(--sd-primary-soft); }
.icon svg { width: 20px; height: 20px; fill: none; stroke: var(--sd-primary); stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
.titles { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.titles strong { font-size: var(--sd-fs-md); color: var(--sd-ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.titles span { font-size: var(--sd-fs-xs); color: var(--sd-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.action { flex: none; }
.body { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; }
</style>
