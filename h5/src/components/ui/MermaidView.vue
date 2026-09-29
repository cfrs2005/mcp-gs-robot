<script lang="ts">
// Module-level (shared by every instance): one lazy mermaid load, one render queue, unique ids.
type Mermaid = typeof import('mermaid')['default']
let loader: Promise<Mermaid> | null = null
let queue: Promise<unknown> = Promise.resolve()
let seq = 0
</script>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import DOMPurify from 'dompurify'
import { t } from '@/i18n'

// ```mermaid fences. mermaid is loaded lazily (its own chunks) the first time a closed fence renders;
// while the fence is still streaming only the source is shown. Output SVG is re-sanitized with DOMPurify
// (svg profile) before insertion; any parse/render error falls back to the source plus one error line.
const props = defineProps<{ source: string; closed: boolean }>()

function token(name: string, fallback: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}
function loadMermaid(): Promise<Mermaid> {
  loader ??= import('mermaid').then(({ default: mermaid }) => {
    const font = token('--sd-font', 'system-ui, sans-serif')
    const ink = token('--sd-ink', '#111c2d')
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'strict',
      theme: 'base',
      fontFamily: font,
      // SVG <text> labels instead of HTML in <foreignObject>, so the svg-profile sanitizer keeps them.
      htmlLabels: false,
      flowchart: { htmlLabels: false },
      // A phone-sized canvas with larger type, so labels stay readable after scaling to ~330px.
      xyChart: { width: 560, height: 360, titleFontSize: 15, xAxis: { labelFontSize: 13, titleFontSize: 13 }, yAxis: { labelFontSize: 13, titleFontSize: 13 } },
      themeVariables: {
        fontFamily: font,
        fontSize: '14px',
        primaryColor: token('--sd-primary-soft', '#e9f1ff'),
        primaryBorderColor: token('--sd-primary', '#2b6ef6'),
        primaryTextColor: ink,
        secondaryColor: token('--sd-surface-2', '#f6f9fe'),
        tertiaryColor: token('--sd-primary-softer', '#f3f7ff'),
        lineColor: token('--sd-muted', '#7a879a'),
        textColor: ink,
        titleColor: ink,
        background: token('--sd-surface', '#ffffff'),
        xyChart: {
          backgroundColor: token('--sd-surface', '#ffffff'),
          titleColor: ink,
          xAxisLabelColor: token('--sd-ink-2', '#3a4a60'),
          yAxisLabelColor: token('--sd-ink-2', '#3a4a60'),
          xAxisLineColor: token('--sd-line-strong', '#d3ddeb'),
          yAxisLineColor: token('--sd-line-strong', '#d3ddeb'),
          plotColorPalette: `${token('--sd-primary', '#2b6ef6')}, ${token('--sd-success', '#16a765')}, ${token('--sd-warning', '#d98a0b')}`,
        },
      },
    })
    return mermaid
  })
  return loader
}

const svg = ref('')
const error = ref('')
const rendering = ref(false)
const wide = ref(0)
const natural = ref(0)
const showSource = ref(false)
let alive = true
onBeforeUnmount(() => { alive = false })

async function render(source: string) {
  rendering.value = true
  error.value = ''
  const id = `sd-mermaid-${++seq}`
  // mermaid.render is not re-entrant: run one diagram at a time.
  const job = queue.then(async () => {
    const mermaid = await loadMermaid()
    try {
      const { svg: raw } = await mermaid.render(id, source)
      return { raw }
    } finally {
      document.getElementById(id)?.remove()
      document.getElementById(`d${id}`)?.remove()
    }
  })
  queue = job.catch(() => undefined)
  try {
    const { raw } = await job
    if (!alive || source !== props.source) return
    const clean = DOMPurify.sanitize(raw, { USE_PROFILES: { svg: true, svgFilters: true } })
    const width = Number(/viewBox="[-\d.]+ [-\d.]+ ([\d.]+)/.exec(clean)?.[1] ?? 0)
    // Wide diagrams keep their natural width (capped) and scroll inside the card instead of shrinking.
    wide.value = width > 720 ? Math.min(width, 1200) : 0
    natural.value = width
    svg.value = clean
  } catch (e) {
    if (!alive) return
    svg.value = ''
    // mermaid parse errors are multi-line ("Parse error on line 3:", snippet, caret, "Expecting …"): keep first and last.
    const lines = (e instanceof Error ? e.message : String(e)).split('\n').map(l => l.trim()).filter(Boolean)
    error.value = [...new Set([lines[0], lines[lines.length - 1]])].join(' ').slice(0, 240)
  } finally {
    if (alive) rendering.value = false
  }
}
watch(() => [props.source, props.closed] as const, ([source, closed]) => { if (closed) void render(source) }, { immediate: true })
</script>

<template>
  <div class="mermaid-card">
    <template v-if="closed && !error">
      <div v-if="rendering && !svg" class="state">{{ t('mermaid.rendering') }}</div>
      <!-- eslint-disable-next-line vue/no-v-html -- mermaid output re-sanitized with DOMPurify (svg profile) -->
      <div v-if="svg" class="canvas" :class="{ wide: wide > 0 }" :style="{ '--mmd-w': `${wide}px`, '--mmd-nat': natural ? `${natural}px` : '100%' }" role="img" :aria-label="t('mermaid.aria')" v-html="svg" />
    </template>
    <div v-if="!closed" class="state">{{ t('html.generating') }}</div>
    <div v-if="error" class="error">{{ t('mermaid.error', { message: error }) }}</div>
    <pre v-if="!closed || error || showSource" class="source"><code>{{ source }}</code></pre>
    <div v-if="closed && !error && svg" class="bar"><button type="button" @click="showSource = !showSource">{{ showSource ? t('mermaid.hideSource') : t('mermaid.showSource') }}</button></div>
  </div>
</template>

<style scoped>
.mermaid-card { min-width: 0; max-width: 100%; margin: 0 0 10px; border-radius: var(--sd-r-md); background: var(--sd-surface); box-shadow: inset 0 0 0 1px var(--sd-line); overflow: hidden; }
.canvas { padding: 12px; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.canvas :deep(svg) { display: block; width: 100%; max-width: min(100%, var(--mmd-nat)) !important; height: auto; margin: 0 auto; font-family: var(--sd-font) !important; }
.canvas.wide :deep(svg) { max-width: none !important; width: var(--mmd-w) !important; }
.state { padding: 10px 12px; color: var(--sd-muted); font-size: var(--sd-fs-xs); }
.error { padding: 9px 12px; background: var(--sd-danger-soft); color: var(--sd-danger); font-size: var(--sd-fs-xs); overflow-wrap: anywhere; }
.source { margin: 0; padding: 12px 14px; background: var(--sd-code-block); color: var(--sd-code-ink); font-family: var(--sd-mono); font-size: 12.5px; line-height: 1.55; overflow-x: auto; white-space: pre; }
.bar { display: flex; justify-content: flex-end; padding: 4px 8px; border-top: 1px solid var(--sd-line); background: var(--sd-surface-2); }
.bar button { border: 0; background: transparent; color: var(--sd-primary); font-size: var(--sd-fs-xs); font-weight: 600; cursor: pointer; padding: 4px 6px; }
</style>
