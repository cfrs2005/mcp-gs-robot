<script setup lang="ts">
import { computed, ref } from 'vue'
import ToolCallCard from './ToolCallCard.vue'
import { resultCard } from './cards/registry'
import { t, tn } from '@/i18n'

export type ToolItem = { id: string; name: string; input: unknown; output?: unknown; isError?: boolean }
const props = defineProps<{ tools: ToolItem[] }>()
const open = ref(false)
const running = computed(() => props.tools.filter((t: ToolItem) => t.output === undefined).length)
const failed = computed(() => props.tools.filter((t: ToolItem) => t.isError).length)
const names = computed(() => [...new Set(props.tools.map((t: ToolItem) => t.name))].join(t('common.listSep')))
// Result cards for successful, mapped tools (cards/registry.ts); the raw JSON stays one tap away above.
const cards = computed(() => props.tools.flatMap(tool => {
  const view = resultCard(tool)
  return view ? [{ tool, view, input: (tool.input && typeof tool.input === 'object' ? tool.input : {}) as Record<string, unknown> }] : []
}))
</script>

<template>
  <div class="tool-block">
    <div class="tool-group" :class="{ open }">
      <button type="button" class="group-title" :aria-expanded="open" @click="open = !open">
        <span class="caret">{{ open ? '▾' : '▸' }}</span>
        <span class="group-label">{{ tn('tools.called', tools.length) }}</span>
        <span class="group-names">{{ names }}</span>
        <span v-if="running" class="group-state run">{{ t('tools.running', { n: running }) }}</span>
        <span v-else-if="failed" class="group-state err">{{ t('tools.failed', { n: failed }) }}</span>
      </button>
      <div v-if="open" class="group-body">
        <ToolCallCard v-for="tool in tools" :key="tool.id" :name="tool.name" :input="tool.input" :output="tool.output" :is-error="tool.isError" />
      </div>
    </div>
    <template v-for="card in cards" :key="card.tool.id">
      <component :is="card.view.component" :name="card.tool.name" :input="card.input" :output="card.view.output" />
      <p v-if="card.view.truncated" class="truncated">{{ t('cards.truncated') }}</p>
    </template>
  </div>
</template>

<style scoped>
.tool-block { display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; min-width: 0; }
.tool-group { border-radius: var(--sd-r-md); background: var(--sd-surface-2); box-shadow: inset 0 0 0 1px var(--sd-line); }
.group-title { display: flex; align-items: center; gap: 8px; width: 100%; min-width: 0; padding: 8px 12px; border: 0; background: transparent; color: var(--sd-ink-2); font-size: var(--sd-fs-sm); text-align: left; cursor: pointer; }
.caret { width: 10px; color: var(--sd-muted); flex: none; }
.group-label { flex: none; font-weight: 600; }
.group-names { flex: 1; min-width: 0; color: var(--sd-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: var(--sd-mono); font-size: var(--sd-fs-xs); }
.group-state { flex: none; font-size: var(--sd-fs-xs); }
.group-state.run { color: var(--sd-warning); }
.group-state.err { color: var(--sd-danger); }
.group-body { padding: 0 8px 8px; }
.truncated { margin: -4px 4px 0; font-size: var(--sd-fs-2xs); color: var(--sd-muted); }
</style>
