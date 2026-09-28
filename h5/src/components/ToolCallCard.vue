<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{ name: string; input: unknown; output?: unknown; isError?: boolean }>()
const open = ref(false)
const prettyInput = computed(() => JSON.stringify(props.input, null, 2))
const prettyOutput = computed(() => JSON.stringify(props.output, null, 2) ?? '')
</script>

<template>
  <div class="tool-card">
    <button class="tool-title" type="button" :aria-expanded="open" @click="open = !open">
      <span>{{ isError ? '调用失败' : '工具调用' }} · {{ name }}</span><span>{{ open ? '收起' : '展开' }}</span>
    </button>
    <div v-if="open" class="tool-content">
      <small>输入</small><pre>{{ prettyInput }}</pre>
      <template v-if="output !== undefined"><small>{{ isError ? '错误' : '结果' }}</small><pre>{{ prettyOutput }}</pre></template>
      <small v-else>执行中…</small>
    </div>
  </div>
</template>

<style scoped>
.tool-card { margin-top: 8px; border: 1px solid #d6e4f4; border-radius: 10px; background: #f8fbff; overflow: hidden; }
.tool-title { display: flex; justify-content: space-between; gap: 12px; width: 100%; padding: 9px; border: 0; background: transparent; color: #286caf; text-align: left; font-size: 12px; cursor: pointer; }
.tool-title span:first-child { overflow-wrap: anywhere; }
.tool-content { padding: 0 9px 9px; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; }
</style>
