<script setup lang="ts">
// Online / offline / warning pill: always a dot plus a text label, never color alone.
defineProps<{ tone: 'ok' | 'off' | 'warn' | 'err'; label: string; solid?: boolean }>()
</script>

<template>
  <span class="pill" :class="[tone, { solid }]"><i class="dot" />{{ label }}</span>
</template>

<style scoped>
.pill { display: inline-flex; align-items: center; gap: 5px; flex: none; height: 22px; padding: 0 8px; border-radius: var(--sd-r-pill); font-size: var(--sd-fs-xs); font-weight: 600; line-height: 1; white-space: nowrap; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.ok { color: var(--sd-success); background: var(--sd-success-soft); }
.off { color: var(--sd-muted); background: var(--sd-surface-2); box-shadow: inset 0 0 0 1px var(--sd-line); }
.warn { color: var(--sd-warning); background: var(--sd-warning-soft); }
.err { color: var(--sd-danger); background: var(--sd-danger-soft); }
.solid.ok { color: var(--sd-on-primary); background: var(--sd-success); }
.solid.ok .dot { background: var(--sd-on-primary); }
</style>
