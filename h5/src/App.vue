<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Tabbar, TabbarItem, Icon, showConfirmDialog } from 'vant'
import { AUTH_REQUIRED_EVENT } from '@/api/client'
import { t } from '@/i18n'

const route = useRoute()
const router = useRouter()
const active = computed(() => route.path.startsWith('/robots') ? '/robots' : route.path)
let prompting = false
async function onAuthRequired() {
  // The settings page reports key validity itself; elsewhere guide the user there once.
  if (prompting || route.path === '/settings') return
  prompting = true
  try {
    await showConfirmDialog({ title: t('auth.title'), message: t('auth.message'), confirmButtonText: t('auth.goSettings') })
    await router.push('/settings')
  } catch { /* cancelled */ } finally { prompting = false }
}
onMounted(() => window.addEventListener(AUTH_REQUIRED_EVENT, onAuthRequired))
onUnmounted(() => window.removeEventListener(AUTH_REQUIRED_EVENT, onAuthRequired))
</script>

<template>
  <div class="app-shell">
    <main class="app-content"><router-view /></main>
    <Tabbar :model-value="active" :safe-area-inset-bottom="true" @change="(path: string) => router.push(path)">
      <TabbarItem name="/chat"><template #icon="{ active: on }"><Icon :name="on ? 'chat' : 'chat-o'" /></template>{{ t('nav.chat') }}</TabbarItem>
      <TabbarItem name="/robots"><template #icon><Icon name="apps-o" /></template>{{ t('nav.robots') }}</TabbarItem>
      <TabbarItem name="/settings"><template #icon="{ active: on }"><Icon :name="on ? 'setting' : 'setting-o'" /></template>{{ t('nav.settings') }}</TabbarItem>
    </Tabbar>
  </div>
</template>

<style>
:root { font-family: var(--sd-font); color: var(--sd-ink); background: var(--sd-bg); -webkit-font-smoothing: antialiased; -webkit-tap-highlight-color: transparent; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--sd-bg); }
button, input, textarea, select { font: inherit; }
.app-shell { min-height: 100dvh; }
.app-content { padding-bottom: calc(var(--van-tabbar-height) + env(safe-area-inset-bottom)); }
.page { max-width: 760px; margin: auto; min-height: calc(100dvh - var(--van-tabbar-height) - env(safe-area-inset-bottom)); background: var(--sd-bg-grad); }
.page-header { min-height: 56px; display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 14px 18px 6px; font-weight: 700; font-size: var(--sd-fs-xl); color: var(--sd-ink); }
.page-body { padding: 12px 14px 16px; }
.panel { border-radius: var(--sd-r-lg); background: var(--sd-surface); padding: 16px; margin-bottom: 12px; box-shadow: var(--sd-shadow-1); }
.panel-title { margin: 0 0 10px; font-size: var(--sd-fs-md); font-weight: 650; color: var(--sd-ink); }
.muted { color: var(--sd-muted); font-size: var(--sd-fs-sm); }
.row { display: flex; align-items: center; gap: 10px; }
.between { justify-content: space-between; }
.stack { display: grid; gap: 10px; }
.empty { padding: 35px 16px; text-align: center; color: var(--sd-muted); font-size: var(--sd-fs-sm); }
.van-tabbar { max-width: 760px; left: 50% !important; transform: translateX(-50%); border-radius: var(--sd-r-lg) var(--sd-r-lg) 0 0; box-shadow: var(--sd-shadow-up); }
.van-tabbar::after { display: none; }
.van-tabbar-item__text { font-weight: 600; }
.van-button { font-weight: 600; }
</style>
