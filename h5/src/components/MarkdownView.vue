<script setup lang="ts">
import { computed } from 'vue'
import { renderSegments } from '@/shared/markdown'
import HtmlPreview from './HtmlPreview.vue'
import MermaidView from './ui/MermaidView.vue'

const props = defineProps<{ text: string }>()
const segments = computed(() => renderSegments(props.text))
</script>

<template>
  <div class="md">
    <template v-for="(segment, index) in segments" :key="index">
      <!-- eslint-disable-next-line vue/no-v-html -- sanitized by DOMPurify in renderSegments -->
      <div v-if="segment.kind === 'md'" class="md-run" v-html="segment.html" />
      <MermaidView v-else-if="segment.kind === 'mermaid'" :source="segment.source" :closed="segment.closed" />
      <HtmlPreview v-else :source="segment.source" :closed="segment.closed" />
    </template>
  </div>
</template>

<style scoped>
.md { min-width: 0; overflow-wrap: anywhere; font-size: 15px; line-height: 1.7; }
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
.md :deep(strong) { font-weight: 650; color: var(--sd-ink); }
.md :deep(a) { color: var(--sd-primary); text-decoration: underline; text-underline-offset: 2px; }
.md :deep(blockquote) { margin: 0 0 10px; padding: 2px 0 2px 12px; border-left: 3px solid var(--sd-line-strong); color: var(--sd-ink-2); }
.md :deep(hr) { border: 0; border-top: 1px solid var(--sd-line); margin: 14px 0; }
.md :deep(code) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.88em; background: var(--sd-code-bg); border-radius: 4px; padding: 1px 5px; }
.md :deep(pre) { margin: 0 0 10px; padding: 12px 14px; border-radius: 10px; background: var(--sd-code-block); color: var(--sd-code-ink); font-size: 12.5px; line-height: 1.55; overflow-x: auto; }
.md :deep(pre code) { background: none; padding: 0; font-size: inherit; color: inherit; }
.md :deep(table) { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 0 0 10px; font-size: 13.5px; line-height: 1.5; }
.md :deep(th), .md :deep(td) { border: 1px solid var(--sd-line); padding: 6px 10px; text-align: left; white-space: nowrap; }
.md :deep(th) { background: var(--sd-surface-2); font-weight: 650; }
.md :deep(tr:nth-child(even) td) { background: var(--sd-surface-2); }
.md :deep(img) { max-width: 100%; }
</style>
