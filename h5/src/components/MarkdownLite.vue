<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ text: string }>()
type Block = { type: 'paragraph' | 'code' | 'list'; lines: string[] }
const blocks = computed<Block[]>(() => {
  const result: Block[] = []
  let code = false
  for (const line of props.text.replace(/\r\n/g, '\n').split('\n')) {
    if (line.trim().startsWith('```')) {
      if (code) code = false
      else { result.push({ type: 'code', lines: [] }); code = true }
      continue
    }
    if (code) { result[result.length - 1].lines.push(line); continue }
    if (!line.trim()) continue
    if (/^\s*[-*] /.test(line)) {
      if (result[result.length - 1]?.type !== 'list') result.push({ type: 'list', lines: [] })
      result[result.length - 1].lines.push(line.replace(/^\s*[-*] /, ''))
    } else {
      if (result[result.length - 1]?.type !== 'paragraph') result.push({ type: 'paragraph', lines: [] })
      result[result.length - 1].lines.push(line)
    }
  }
  return result
})
</script>

<template>
  <div class="markdown-lite">
    <template v-for="(block, index) in blocks" :key="index">
      <pre v-if="block.type === 'code'"><code>{{ block.lines.join('\n') }}</code></pre>
      <ul v-else-if="block.type === 'list'"><li v-for="(line, i) in block.lines" :key="i">{{ line }}</li></ul>
      <p v-else>{{ block.lines.join('\n') }}</p>
    </template>
  </div>
</template>

<style scoped>
.markdown-lite { overflow-wrap: anywhere; }
p { margin: 0 0 9px; white-space: pre-wrap; }
p:last-child, ul:last-child, pre:last-child { margin-bottom: 0; }
ul { margin: 0 0 9px; padding-left: 21px; }
pre { overflow: auto; margin: 0 0 9px; padding: 10px; border-radius: 8px; background: #172a3f; color: #e4edf8; font-size: 12px; }
</style>
