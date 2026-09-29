<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { robotModel } from '@/shared/robotModels'

// Product photo by model when known; otherwise (or when the remote image fails) a drawn generic robot.
const props = defineProps<{ info?: { modelTypeCode?: unknown; displayName?: unknown } | null; alt?: string }>()
const model = computed(() => robotModel(props.info))
const failed = ref(false)
watch(() => model.value?.image, () => { failed.value = false })
</script>

<template>
  <div class="robot-image">
    <img v-if="model && !failed" :src="model.image" :alt="alt || model.name" referrerpolicy="no-referrer" loading="lazy" decoding="async" @error="failed = true">
    <svg v-else viewBox="0 0 96 96" role="img" :aria-label="alt || 'robot'">
      <ellipse cx="48" cy="88" rx="30" ry="4" class="shadow" />
      <rect x="26" y="10" width="44" height="10" rx="4" class="dark" />
      <rect x="22" y="18" width="52" height="46" rx="12" class="body" />
      <rect x="29" y="25" width="38" height="20" rx="7" class="dark" />
      <path d="M36 37c1.6-3.6 6.4-3.6 8 0M52 37c1.6-3.6 6.4-3.6 8 0" class="eye" />
      <rect x="20" y="60" width="56" height="20" rx="7" class="dark" />
      <circle cx="31" cy="80" r="5" class="wheel" /><circle cx="65" cy="80" r="5" class="wheel" />
      <rect x="40" y="51" width="16" height="4" rx="2" class="accent" />
    </svg>
  </div>
</template>

<style scoped>
.robot-image { display: grid; place-items: center; overflow: hidden; }
img { width: 100%; height: 100%; object-fit: contain; }
svg { width: 82%; height: 82%; }
.shadow { fill: var(--sd-ink); opacity: .08; }
.dark { fill: var(--sd-mark-shell); }
.body { fill: var(--sd-surface); stroke: var(--sd-line-strong); stroke-width: 1.5; }
.eye { fill: none; stroke: var(--sd-primary); stroke-width: 3; stroke-linecap: round; }
.wheel { fill: var(--sd-ink-2); }
.accent { fill: var(--sd-primary); }
</style>
