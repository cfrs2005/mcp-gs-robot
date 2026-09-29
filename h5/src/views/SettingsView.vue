<script setup lang="ts">
import { KEYS } from '@/storageKeys'
import { onMounted, ref } from 'vue'
import { Button, CellGroup, Field, Radio, RadioGroup, showConfirmDialog, showFailToast, showSuccessToast } from 'vant'
import { ApiError, authCheck, deleteAgentSession, health, type Health } from '@/api/client'
import { useSettingsStore } from '@/stores/settings'
import { LOCALES, locale, setLocale, t, type Locale } from '@/i18n'

const settings = useSettingsStore()
const apiBase = ref(settings.apiBase)
const apiKey = ref(settings.apiKey)
const checking = ref(false)
const result = ref<Health | null>(null)
const authRequired = ref(false)
const keyState = ref<'ok' | 'invalid' | null>(null)
async function loadHealth() {
  result.value = await health()
  authRequired.value = !!result.value.auth_required
}
// Protected, side-effect-free probe: 200 means the saved key is accepted.
async function verifyKey(): Promise<boolean> {
  try {
    await authCheck()
    keyState.value = 'ok'
    showSuccessToast(t('settings.connected'))
    return true
  } catch (e) {
    keyState.value = e instanceof ApiError && e.code === 401 ? 'invalid' : null
    showFailToast(keyState.value === 'invalid' ? t('settings.keyInvalid') : e instanceof Error ? e.message : t('settings.connectFailed'))
    return false
  }
}
async function save() {
  settings.save(apiBase.value, apiKey.value)
  showSuccessToast(t('settings.saved'))
  checking.value = true
  try { await verifyKey() } finally { checking.value = false }
}
async function test() {
  settings.save(apiBase.value, apiKey.value)
  checking.value = true
  try {
    await loadHealth()
    await verifyKey()
  } catch (e) { result.value = null; showFailToast(e instanceof Error ? e.message : t('settings.connectFailed')) }
  finally { checking.value = false }
}
onMounted(() => { loadHealth().catch(() => { result.value = null }) })
async function clearChat() {
  try {
    await showConfirmDialog({ title: t('settings.clearTitle'), message: t('settings.clearMessage') })
    const id = localStorage.getItem(KEYS.sessionId)
    if (id) await deleteAgentSession(id)
    localStorage.removeItem(KEYS.sessionId)
    window.dispatchEvent(new Event('saodi:clear-chat'))
    showSuccessToast(t('settings.cleared'))
  } catch (e) {
    if (e !== 'cancel') showFailToast(e instanceof Error ? e.message : t('settings.clearFailed'))
  }
}
</script>

<template>
  <div class="page">
    <header class="page-header">{{ t('settings.title') }}</header>
    <div class="page-body">
      <div class="panel">
        <CellGroup inset>
          <Field :label="t('settings.language')">
            <template #input>
              <RadioGroup :model-value="locale" direction="horizontal" @update:model-value="(value: Locale) => setLocale(value)">
                <Radio v-for="code in LOCALES" :key="code" :name="code">{{ t(`lang.${code}`) }}</Radio>
              </RadioGroup>
            </template>
          </Field>
        </CellGroup>
      </div>
      <div class="panel">
        <CellGroup inset>
          <Field v-model="apiBase" :label="t('settings.apiBase')" :placeholder="t('settings.apiBasePlaceholder')" inputmode="url" />
          <Field v-model="apiKey" :label="t('settings.apiKey')" type="password" :required="authRequired" :placeholder="authRequired ? t('settings.apiKeyRequired') : t('settings.apiKeyOptional')" />
        </CellGroup>
        <p v-if="authRequired" class="muted key-hint">{{ t('settings.keyHint') }}</p>
        <p class="muted">{{ t('settings.keyLocal') }}</p>
        <div class="row"><Button type="primary" size="small" @click="save">{{ t('settings.save') }}</Button><Button size="small" :loading="checking" @click="test">{{ t('settings.test') }}</Button></div>
        <div v-if="keyState" class="connection" :class="{ invalid: keyState === 'invalid' }">{{ keyState === 'ok' ? t('settings.connected') : t('settings.keyInvalid') }}</div>
        <div v-if="result" class="connection">{{ t('settings.healthLine', { version: result.version, provider: result.agent_provider, tools: result.tools }) }}</div>
      </div>
      <div class="panel"><Button type="danger" plain block @click="clearChat">{{ t('settings.clearChat') }}</Button></div>
    </div>
  </div>
</template>

<style scoped>
.connection { margin-top: 16px; font-size: 13px; color: #427755; }
.connection.invalid { color: #c9483c; }
.key-hint { color: #b7791f; }
</style>
