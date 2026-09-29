<script setup lang="ts">
import { computed, ref } from 'vue'
import { t } from '@/i18n'

const props = defineProps<{ name: string; input: unknown; output?: unknown; isError?: boolean }>()
const open = ref(false)
const prettyInput = computed(() => JSON.stringify(props.input, null, 2))
const prettyOutput = computed(() => typeof props.output === 'string' ? props.output : JSON.stringify(props.output, null, 2) ?? '')
const state = computed(() => props.output === undefined ? 'run' : props.isError ? 'err' : 'ok')
</script>

<template>
  <div class="tool-card">
    <button class="tool-title" type="button" :aria-expanded="open" @click="open = !open">
      <span class="dot" :class="state" /><span class="tool-name">{{ isError ? t('tool.callFailed') : t('tool.call') }} · {{ name }}</span><span class="tool-toggle">{{ open ? t('tool.collapse') : t('tool.expand') }}</span>
    </button>
    <div v-if="open" class="tool-content">
      <small>{{ t('tool.input') }}</small><pre>{{ prettyInput }}</pre>
      <template v-if="output !== undefined"><small>{{ isError ? t('tool.error') : t('tool.result') }}</small><pre>{{ prettyOutput }}</pre></template>
      <small v-else>{{ t('tool.running') }}</small>
    </div>
  </div>
</template>

<style scoped>
.tool-card { border: 1px solid var(--sd-line); border-radius: 9px; background: var(--sd-surface); overflow: hidden; }
.tool-card + .tool-card { margin-top: 6px; }
.tool-title { display: flex; align-items: center; gap: 8px; width: 100%; padding: 7px 10px; border: 0; background: transparent; color: var(--sd-ink-2); text-align: left; font-size: 12.5px; cursor: pointer; }
.tool-name { flex: 1; overflow-wrap: anywhere; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.tool-toggle { color: var(--sd-primary); flex: none; }
.dot { width: 7px; height: 7px; border-radius: 50%; flex: none; background: var(--sd-faint); }
.dot.ok { background: var(--sd-success); }
.dot.err { background: var(--sd-danger); }
.dot.run { background: var(--sd-warning); animation: pulse 1s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: .35; } }
.tool-content { padding: 0 10px 10px; }
.tool-content small { color: var(--sd-muted); }
pre { margin: 4px 0 8px; padding: 8px 10px; border-radius: 7px; background: var(--sd-bg); white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; line-height: 1.5; }
</style>
