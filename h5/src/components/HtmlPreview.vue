<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { localeTag, t } from '@/i18n'

// Model-written HTML runs only inside sandbox="allow-scripts" (opaque origin, never allow-same-origin),
// so it cannot read this app's localStorage (API Key), cookies or DOM.
const props = defineProps<{ source: string; closed: boolean }>()
const tab = ref<'preview' | 'source'>(props.closed ? 'preview' : 'source')
watch(() => props.closed, (closed: boolean) => { if (closed) tab.value = 'preview' })

const CAP = 520
const frame = ref<HTMLIFrameElement | null>(null)
const reported = ref(0)
const expanded = ref(false)
const height = computed(() => {
  const h = reported.value || 240
  return expanded.value ? h : Math.min(h, CAP)
})

// Measure the body, not documentElement.scrollHeight: the latter never drops below the iframe's own height.
const reporter = `<script>(function(){function s(){var b=document.body;if(!b)return;var m=parseFloat(getComputedStyle(b).marginBottom)||0;
parent.postMessage({type:'saodi-html-height',height:Math.ceil(b.getBoundingClientRect().bottom+m)},'*')}
addEventListener('load',s);if(window.ResizeObserver&&document.body)new ResizeObserver(s).observe(document.body);s()})()<\/script>`
const srcdoc = computed(() => `${props.source}\n${reporter}`)

function onMessage(event: MessageEvent) {
  if (!frame.value || event.source !== frame.value.contentWindow) return
  const data = event.data as { type?: string; height?: unknown }
  if (data?.type === 'saodi-html-height' && typeof data.height === 'number' && Number.isFinite(data.height)) {
    reported.value = Math.max(60, Math.min(data.height, 4000))
  }
}
onMounted(() => window.addEventListener('message', onMessage))
onUnmounted(() => window.removeEventListener('message', onMessage))

const escapeAttr = (value: string) => value.replace(/&/g, '&amp;').replace(/"/g, '&quot;')
// The blob page is same-origin, so it contains only our static wrapper; the model HTML lives in a
// nested sandboxed iframe and keeps the opaque origin there too.
function openWindow() {
  const page = `<!doctype html><html lang="${localeTag.value}"><head><meta charset="utf-8"><title>${escapeAttr(t('html.frameTitle'))}</title>`
    + `<style>html,body{margin:0;height:100%}iframe{border:0;width:100%;height:100%;display:block}</style></head>`
    + `<body><iframe sandbox="allow-scripts" srcdoc="${escapeAttr(props.source)}"></iframe></body></html>`
  const url = URL.createObjectURL(new Blob([page], { type: 'text/html' }))
  window.open(url, '_blank', 'noopener')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
</script>

<template>
  <div class="html-card">
    <div class="html-bar">
      <span class="html-tag">HTML</span>
      <div class="html-tabs" role="tablist">
        <button type="button" role="tab" :aria-selected="tab === 'preview'" :disabled="!closed" :class="{ on: tab === 'preview' }" @click="tab = 'preview'">{{ t('html.preview') }}</button>
        <button type="button" role="tab" :aria-selected="tab === 'source'" :class="{ on: tab === 'source' }" @click="tab = 'source'">{{ t('html.source') }}</button>
      </div>
      <button v-if="closed" type="button" class="html-open" @click="openWindow">{{ t('html.openWindow') }}</button>
      <span v-else class="html-wait">{{ t('html.generating') }}</span>
    </div>
    <template v-if="tab === 'preview' && closed">
      <iframe ref="frame" class="html-frame" sandbox="allow-scripts" :srcdoc="srcdoc" :style="{ height: `${height}px` }" :title="t('html.frameTitle')" />
      <button v-if="reported > CAP" type="button" class="html-more" @click="expanded = !expanded">{{ expanded ? t('html.collapse') : t('html.expandAll', { px: reported }) }}</button>
    </template>
    <pre v-else class="html-source"><code>{{ source }}</code></pre>
  </div>
</template>

<style scoped>
.html-card { border: 1px solid var(--sd-line); border-radius: 12px; overflow: hidden; background: var(--sd-surface); margin: 0 0 10px; }
.html-bar { display: flex; align-items: center; gap: 10px; padding: 6px 8px 6px 12px; border-bottom: 1px solid var(--sd-line); background: var(--sd-surface-2); font-size: 12.5px; }
.html-tag { font-weight: 650; color: var(--sd-ink-2); letter-spacing: .04em; }
.html-tabs { display: flex; background: var(--sd-code-bg); border-radius: 7px; padding: 2px; }
.html-tabs button { border: 0; background: transparent; padding: 3px 10px; border-radius: 5px; color: var(--sd-ink-2); cursor: pointer; font-size: 12.5px; }
.html-tabs button.on { background: var(--sd-surface); color: var(--sd-ink); box-shadow: var(--sd-shadow-1); }
.html-tabs button:disabled { opacity: .45; cursor: default; }
.html-open { margin-left: auto; border: 0; background: transparent; color: var(--sd-primary); cursor: pointer; font-size: 12.5px; }
.html-wait { margin-left: auto; color: var(--sd-muted); }
.html-frame { display: block; width: 100%; border: 0; background: var(--sd-surface); }
.html-more { display: block; width: 100%; border: 0; border-top: 1px solid var(--sd-line); background: var(--sd-surface-2); padding: 6px; color: var(--sd-primary); cursor: pointer; font-size: 12.5px; }
.html-source { margin: 0; padding: 12px 14px; background: var(--sd-code-block); color: var(--sd-code-ink); font-size: 12.5px; line-height: 1.55; overflow-x: auto; }
</style>
