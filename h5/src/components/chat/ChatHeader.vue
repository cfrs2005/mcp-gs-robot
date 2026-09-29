<script setup lang="ts">
import markUrl from '@/shared/mark.svg'
import { t } from '@/i18n'

// History · brand with service status (from /health; null while checking) · New chat.
defineProps<{ busy: boolean; online: boolean | null }>()
const emit = defineEmits<{ history: []; new: [] }>()
</script>

<template>
  <header class="chat-header">
    <div class="bar">
      <button type="button" class="pill-btn" :aria-label="t('chat.historyAria')" @click="emit('history')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M5 12h14M5 17h9" /></svg><span>{{ t('chat.history') }}</span>
      </button>
      <div class="brand">
        <img :src="markUrl" alt="" class="mark">
        <div class="brand-text">
          <strong>{{ t('brand.name') }}</strong>
          <span class="status" :class="online === null ? 'wait' : online ? 'on' : 'off'"><i />{{ online === null ? t('chat.statusChecking') : online ? t('chat.statusOnline') : t('chat.statusOffline') }}</span>
        </div>
      </div>
      <button type="button" class="pill-btn primary" :disabled="busy" @click="emit('new')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg><span>{{ t('chat.new') }}</span>
      </button>
    </div>
    <p class="tagline">{{ t('brand.tagline') }}</p>
  </header>
</template>

<style scoped>
.chat-header { padding: 10px 0 8px; }
.bar { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 8px; }
.pill-btn { justify-self: start; display: inline-flex; align-items: center; gap: 5px; height: 36px; padding: 0 12px 0 10px; border: 1px solid var(--sd-line-strong); border-radius: var(--sd-r-md); background: var(--sd-surface); color: var(--sd-ink); font-size: var(--sd-fs-sm); font-weight: 600; cursor: pointer; box-shadow: var(--sd-shadow-1); white-space: nowrap; }
.pill-btn svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
.pill-btn.primary { justify-self: end; border-color: var(--sd-primary); color: var(--sd-primary); }
.pill-btn:disabled { opacity: .5; cursor: default; }
.brand { display: flex; align-items: center; gap: 8px; min-width: 0; }
.mark { width: 34px; height: 34px; flex: none; }
.brand-text { display: flex; flex-direction: column; min-width: 0; }
.brand-text strong { font-size: var(--sd-fs-lg); line-height: 1.15; color: var(--sd-ink); white-space: nowrap; }
.status { display: inline-flex; align-items: center; gap: 4px; font-size: var(--sd-fs-xs); font-weight: 600; }
.status i { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.status.on { color: var(--sd-success); }
.status.off { color: var(--sd-danger); }
.status.wait { color: var(--sd-muted); }
.tagline { margin: 4px 0 0; text-align: center; font-size: var(--sd-fs-xs); color: var(--sd-muted); }
@media (max-width: 360px) { .pill-btn span { display: none; } .pill-btn { padding: 0 9px; } }
</style>
