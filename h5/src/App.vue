<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Tabbar, TabbarItem, Icon } from 'vant'

const route = useRoute()
const router = useRouter()
const active = computed(() => route.path.startsWith('/robots') ? '/robots' : route.path)
</script>

<template>
  <div class="app-shell">
    <main class="app-content"><router-view /></main>
    <Tabbar :model-value="active" :safe-area-inset-bottom="true" @change="(path: string) => router.push(path)">
      <TabbarItem name="/chat"><template #icon><Icon name="chat-o" /></template>对话</TabbarItem>
      <TabbarItem name="/robots"><template #icon><Icon name="apps-o" /></template>机器人</TabbarItem>
      <TabbarItem name="/settings"><template #icon><Icon name="setting-o" /></template>设置</TabbarItem>
    </Tabbar>
  </div>
</template>

<style>
:root { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif; color: #1c3146; background: #f4f7fb; }
* { box-sizing: border-box; }
body { margin: 0; }
button, input, textarea { font: inherit; }
.app-shell { min-height: 100dvh; }
.app-content { padding-bottom: calc(58px + env(safe-area-inset-bottom)); }
.page { max-width: 760px; margin: auto; }
.page-header { min-height: 55px; display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; background: #fff; font-weight: 700; font-size: 18px; }
.page-body { padding: 14px; }
.panel { border-radius: 14px; background: #fff; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 12px #173a630a; }
.muted { color: #7d8998; font-size: 13px; }
.row { display: flex; align-items: center; gap: 10px; }
.between { justify-content: space-between; }
.stack { display: grid; gap: 10px; }
.empty { padding: 35px 16px; text-align: center; color: #8a97a5; }
.van-tabbar { max-width: 760px; left: 50% !important; transform: translateX(-50%); }
</style>
