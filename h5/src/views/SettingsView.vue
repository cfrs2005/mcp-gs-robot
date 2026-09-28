<script setup lang="ts">
import { ref } from 'vue'
import { Button, CellGroup, Field, showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import { deleteAgentSession, health, type Health } from '@/api/client'
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
const apiBase = ref(settings.apiBase)
const apiKey = ref(settings.apiKey)
const checking = ref(false)
const result = ref<Health | null>(null)
function save() {
  settings.save(apiBase.value, apiKey.value)
  showSuccessToast('设置已保存')
}
async function test() {
  settings.save(apiBase.value, apiKey.value)
  checking.value = true
  try {
    result.value = await health()
    showSuccessToast('连接成功')
  } catch (e) { result.value = null; showFailToast(e instanceof Error ? e.message : '连接失败') }
  finally { checking.value = false }
}
async function clearChat() {
  try {
    await showConfirmDialog({ title: '清除对话', message: '删除当前对话记录？' })
    const id = localStorage.getItem('pi.sessionId')
    if (id) await deleteAgentSession(id)
    localStorage.removeItem('pi.sessionId')
    window.dispatchEvent(new Event('pi:clear-chat'))
    showSuccessToast('对话已清除')
  } catch (e) {
    if (e !== 'cancel') showFailToast(e instanceof Error ? e.message : '清除失败')
  }
}
</script>

<template>
  <div class="page">
    <header class="page-header">设置</header>
    <div class="page-body">
      <div class="panel">
        <CellGroup inset>
          <Field v-model="apiBase" label="API Base URL" placeholder="留空使用同源服务" inputmode="url" />
          <Field v-model="apiKey" label="API Key" type="password" placeholder="选填" />
        </CellGroup>
        <p class="muted">密钥仅保存在此浏览器的 localStorage 中。</p>
        <div class="row"><Button type="primary" size="small" @click="save">保存</Button><Button size="small" :loading="checking" @click="test">测试连接</Button></div>
        <div v-if="result" class="connection">版本 {{ result.version }} · Provider {{ result.agent_provider }} · 工具 {{ result.tools }} 个</div>
      </div>
      <div class="panel"><Button type="danger" plain block @click="clearChat">清除对话</Button></div>
    </div>
  </div>
</template>

<style scoped>
.connection { margin-top: 16px; font-size: 13px; color: #427755; }
</style>
