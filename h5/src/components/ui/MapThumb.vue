<script setup lang="ts">
import { ref, watch } from 'vue'
import { t } from '@/i18n'

// Map image from an upstream URL. Signed URLs expire and some hosts refuse cross-site loads,
// so a failed load shows a placeholder instead of a broken image.
const props = defineProps<{ src?: string | null; caption?: string; tall?: boolean }>()
const failed = ref(false)
watch(() => props.src, () => { failed.value = false })
</script>

<template>
  <figure class="map-thumb" :class="{ tall }">
    <img v-if="src && !failed" :src="src" :alt="caption || t('cards.mapAlt')" referrerpolicy="no-referrer" loading="lazy" @error="failed = true">
    <div v-else class="placeholder">
      <svg viewBox="0 0 48 48" aria-hidden="true"><path d="M6 12l12-5 12 5 12-5v29l-12 5-12-5-12 5z" /><path d="M18 7v29M30 12v29" /></svg>
      <span>{{ src ? t('cards.mapUnavailable') : t('detail.noMapImage') }}</span>
    </div>
    <figcaption v-if="caption">{{ caption }}</figcaption>
  </figure>
</template>

<style scoped>
.map-thumb { margin: 0; border-radius: var(--sd-r-md); overflow: hidden; background: var(--sd-primary-softer); box-shadow: inset 0 0 0 1px var(--sd-line); }
img { display: block; width: 100%; max-height: 220px; object-fit: contain; background: var(--sd-surface); }
.tall img { max-height: 420px; }
.placeholder { display: grid; place-items: center; gap: 6px; min-height: 110px; padding: 16px; color: var(--sd-muted); font-size: var(--sd-fs-xs); text-align: center; }
.placeholder svg { width: 30px; height: 30px; fill: none; stroke: var(--sd-faint); stroke-width: 2; stroke-linejoin: round; }
figcaption { padding: 7px 10px; font-size: var(--sd-fs-xs); color: var(--sd-ink-2); background: var(--sd-surface); border-top: 1px solid var(--sd-line); overflow-wrap: anywhere; }
</style>
