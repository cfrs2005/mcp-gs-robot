<script setup lang="ts">
import { computed } from 'vue'
import CardShell from '@/components/ui/CardShell.vue'
import MapThumb from '@/components/ui/MapThumb.vue'
import { t } from '@/i18n'

// get_map_canvas → { mapPng: { downloadUri, exist }, mapInfo }
// get_task_report_map_images → { list: [{ url, map_image_id }] }
const props = defineProps<{ input: Record<string, unknown>; output: unknown; name: string }>()
const images = computed(() => {
  const out = props.output as { mapPng?: { downloadUri?: unknown; exist?: unknown }; list?: unknown } | null
  if (out?.mapPng) return out.mapPng.exist !== false && typeof out.mapPng.downloadUri === 'string' ? [{ key: 'canvas', src: out.mapPng.downloadUri, caption: '' }] : [{ key: 'none', src: '', caption: '' }]
  const list = Array.isArray(out?.list) ? out.list as { url?: unknown; map_image_id?: unknown }[] : []
  return list.slice(0, 4).map((item, i) => ({ key: String(item.map_image_id ?? i), src: typeof item.url === 'string' ? item.url : '', caption: list.length > 1 ? `#${i + 1}` : '' }))
})
const subtitle = computed(() => [props.input.robot_sn, props.input.map_id ?? props.input.task_report_id].filter(v => typeof v === 'string').join(' · '))
const title = computed(() => props.name === 'get_map_canvas' ? t('detail.canvas') : t('cards.reportMap'))
</script>

<template>
  <CardShell :title="title" :subtitle="subtitle" icon="map">
    <div class="maps" :class="{ grid: images.length > 1 }">
      <MapThumb v-for="img in images" :key="img.key" :src="img.src" :caption="img.caption" />
    </div>
  </CardShell>
</template>

<style scoped>
.maps { display: grid; grid-template-columns: minmax(0, 1fr); gap: 8px; }
.maps.grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
</style>
