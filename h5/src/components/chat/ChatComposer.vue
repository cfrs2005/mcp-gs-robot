<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { t } from '@/i18n'

// Rounded input + round send button. Enter sends, Shift+Enter adds a line; the box grows up to ~5 lines.
const draft = defineModel<string>({ required: true })
const props = defineProps<{ disabled: boolean }>()
const emit = defineEmits<{ send: [] }>()
const box = ref<HTMLTextAreaElement | null>(null)
function fit() {
  const el = box.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 124)}px`
}
watch(draft, () => void nextTick(fit))
function submit() { if (!props.disabled && draft.value.trim()) emit('send') }
defineExpose({ focus: () => box.value?.focus() })
</script>

<template>
  <form class="composer" @submit.prevent="submit">
    <textarea ref="box" v-model="draft" rows="1" :placeholder="t('chat.placeholder')" :aria-label="t('chat.inputAria')" @keydown.enter.exact.prevent="submit" />
    <button type="submit" class="send" :disabled="disabled || !draft.trim()" :aria-label="t('chat.send')" :title="t('chat.send')">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 3.5L10 14M20.5 3.5l-6.3 17-4.2-6.5-6.5-4.2z" /></svg>
    </button>
  </form>
</template>

<style scoped>
.composer { display: flex; align-items: flex-end; gap: 10px; padding: 6px 6px 6px 16px; border-radius: var(--sd-r-xl); background: var(--sd-surface); box-shadow: var(--sd-shadow-2); }
textarea { flex: 1; resize: none; min-height: 40px; max-height: 124px; padding: 9px 0; border: 0; outline: 0; background: transparent; color: var(--sd-ink); font-size: var(--sd-fs-md); line-height: 22px; }
textarea::placeholder { color: var(--sd-faint); }
.send { flex: none; display: grid; place-items: center; width: 44px; height: 44px; border: 0; border-radius: 50%; background: var(--sd-primary); box-shadow: var(--sd-shadow-primary); cursor: pointer; transition: transform .1s, opacity .15s; }
.send:active { transform: scale(.94); }
.send:disabled { opacity: .45; box-shadow: none; cursor: default; }
.send svg { width: 21px; height: 21px; fill: none; stroke: var(--sd-on-primary); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
</style>
