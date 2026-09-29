<script setup lang="ts">
import { computed } from 'vue'
import { renderSegments } from '@/markdown'
import HtmlPreview from './HtmlPreview.vue'

const props = defineProps<{ text: string }>()
const segments = computed(() => renderSegments(props.text))
</script>

<template>
  <div class="md">
    <template v-for="(segment, index) in segments" :key="index">
      <!-- eslint-disable-next-line vue/no-v-html -- sanitized by DOMPurify in renderSegments -->
      <div v-if="segment.kind === 'md'" class="md-run" v-html="segment.html" />
      <HtmlPreview v-else :source="segment.source" :closed="segment.closed" />
    </template>
  </div>
</template>

<style scoped>
.md { overflow-wrap: anywhere; font-size: 15px; line-height: 1.7; }
.md-run :deep(> :first-child) { margin-top: 0; }
.md-run :deep(> :last-child) { margin-bottom: 0; }
.md > * + * { margin-top: 12px; }
.md :deep(p) { margin: 0 0 10px; }
.md :deep(h1), .md :deep(h2), .md :deep(h3), .md :deep(h4) { margin: 18px 0 8px; line-height: 1.35; font-weight: 650; }
.md :deep(h1) { font-size: 20px; }
.md :deep(h2) { font-size: 18px; }
.md :deep(h3) { font-size: 16px; }
.md :deep(h4) { font-size: 15px; }
.md :deep(ul), .md :deep(ol) { margin: 0 0 10px; padding-left: 22px; }
.md :deep(li) { margin: 2px 0; }
.md :deep(li > p) { margin: 0; }
.md :deep(strong) { font-weight: 650; color: #10263c; }
.md :deep(a) { color: #1f6fbf; text-decoration: underline; text-underline-offset: 2px; }
.md :deep(blockquote) { margin: 0 0 10px; padding: 2px 0 2px 12px; border-left: 3px solid #c9d8ea; color: #50637a; }
.md :deep(hr) { border: 0; border-top: 1px solid #dfe7f0; margin: 14px 0; }
.md :deep(code) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.88em; background: #e8eef6; border-radius: 4px; padding: 1px 5px; }
.md :deep(pre) { margin: 0 0 10px; padding: 12px 14px; border-radius: 10px; background: #172a3f; color: #e4edf8; font-size: 12.5px; line-height: 1.55; overflow-x: auto; }
.md :deep(pre code) { background: none; padding: 0; font-size: inherit; color: inherit; }
.md :deep(table) { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 0 0 10px; font-size: 13.5px; line-height: 1.5; }
.md :deep(th), .md :deep(td) { border: 1px solid #dbe4ee; padding: 6px 10px; text-align: left; white-space: nowrap; }
.md :deep(th) { background: #edf3f9; font-weight: 650; }
.md :deep(tr:nth-child(even) td) { background: #f8fafd; }
.md :deep(img) { max-width: 100%; }
</style>
