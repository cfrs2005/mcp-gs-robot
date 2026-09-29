<script setup lang="ts">
import { computed, ref } from 'vue'
import ToolCallCard from './ToolCallCard.vue'
import { t, tn } from '@/i18n'

export type ToolItem = { id: string; name: string; input: unknown; output?: unknown; isError?: boolean }
const props = defineProps<{ tools: ToolItem[] }>()
const open = ref(false)
const running = computed(() => props.tools.filter((t: ToolItem) => t.output === undefined).length)
const failed = computed(() => props.tools.filter((t: ToolItem) => t.isError).length)
const names = computed(() => [...new Set(props.tools.map((t: ToolItem) => t.name))].join(t('common.listSep')))
</script>

<template>
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
</template>

<style scoped>
.tool-group { border-radius: 10px; background: #eaf0f7; }
.group-title { display: flex; align-items: center; gap: 8px; width: 100%; min-width: 0; padding: 8px 12px; border: 0; background: transparent; color: #33506e; font-size: 13px; text-align: left; cursor: pointer; }
.caret { width: 10px; color: #6d819a; flex: none; }
.group-label { flex: none; font-weight: 600; }
.group-names { flex: 1; min-width: 0; color: #6d819a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
.group-state { flex: none; font-size: 12px; }
.group-state.run { color: #b7801a; }
.group-state.err { color: #c2403c; }
.group-body { padding: 0 8px 8px; }
</style>
