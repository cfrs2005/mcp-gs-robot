<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button, Icon, Popup, showConfirmDialog, showFailToast, showToast } from 'vant'
import { ApiError, deleteAgentSession, listAgentSessions, type SessionSummary } from '@/api/client'
import { relativeTime, t, tn } from '@/i18n'

const props = defineProps<{ show: boolean; currentId: string; busy: boolean }>()
const emit = defineEmits<{ 'update:show': [value: boolean]; select: [id: string]; deleted: [id: string]; new: [] }>()
const items = ref<SessionSummary[]>([])
const loading = ref(false)
const failed = ref('')

async function load() {
  loading.value = true
  failed.value = ''
  try { items.value = (await listAgentSessions()).items }
  catch (e) { failed.value = e instanceof Error ? e.message : t('history.loadFailed') }
  finally { loading.value = false }
}
watch(() => props.show, open => { if (open) void load() })

function pick(item: SessionSummary) {
  if (props.busy && item.session_id !== props.currentId) { showToast(t('history.busySwitch')); return }
  emit('select', item.session_id)
  emit('update:show', false)
}
function startNew() {
  emit('update:show', false)
  emit('new')
}
async function remove(item: SessionSummary) {
  try {
    await showConfirmDialog({ title: t('history.deleteTitle'), message: t('history.deleteMessage', { title: item.title || t('history.untitled') }) })
  } catch { return }
  try {
    await deleteAgentSession(item.session_id)
    items.value = items.value.filter(i => i.session_id !== item.session_id)
    emit('deleted', item.session_id)
    showToast(t('history.deleted'))
  } catch (e) {
    if (e instanceof ApiError && Number(e.code) === 409) showToast(t('history.deleteBusy'))
    else if (e instanceof ApiError && Number(e.code) === 404) {
      items.value = items.value.filter(i => i.session_id !== item.session_id)
      emit('deleted', item.session_id)
    } else showFailToast(e instanceof Error ? e.message : t('history.deleteFailed'))
  }
}
</script>

<template>
  <Popup :show="show" position="left" class="history-drawer" :style="{ height: '100%' }" @update:show="(v: boolean) => emit('update:show', v)">
    <div class="drawer">
      <div class="drawer-head">
        <span>{{ t('history.title') }}</span>
        <Button size="small" plain type="primary" :disabled="busy" @click="startNew">{{ t('history.new') }}</Button>
      </div>
      <div class="drawer-body">
        <div v-if="loading && !items.length" class="empty">{{ t('common.loading') }}</div>
        <div v-else-if="failed" class="empty">{{ failed }}<br><Button size="small" class="retry" @click="load">{{ t('common.retry') }}</Button></div>
        <div v-else-if="!items.length" class="empty">{{ t('history.empty') }}</div>
        <ul v-else class="list">
          <li v-for="item in items" :key="item.session_id" class="item" :class="{ current: item.session_id === currentId }">
            <button type="button" class="item-main" @click="pick(item)">
              <span class="title">{{ item.title || t('history.untitled') }}</span>
              <span class="meta">{{ relativeTime(item.updated_at) }} · {{ tn('history.messages', item.message_count) }}</span>
            </button>
            <button type="button" class="item-del" :aria-label="t('history.deleteAria')" @click="remove(item)"><Icon name="delete-o" /></button>
          </li>
        </ul>
      </div>
    </div>
  </Popup>
</template>

<style scoped>
.history-drawer { width: min(86vw, 340px); }
.drawer { height: 100%; display: flex; flex-direction: column; background: #f4f7fb; }
.drawer-head { display: flex; align-items: center; justify-content: space-between; min-height: 55px; padding: 12px 16px; background: #fff; border-bottom: 1px solid #e8eef5; font-weight: 700; font-size: 17px; }
.drawer-body { flex: 1; overflow-y: auto; padding: 10px; }
.retry { margin-top: 10px; }
.list { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
.item { display: flex; align-items: stretch; border-radius: 10px; background: #fff; box-shadow: 0 2px 10px #173a630a; }
.item.current { background: #d9edff; }
.item-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; padding: 10px 12px; border: 0; background: transparent; text-align: left; cursor: pointer; color: inherit; }
.title { font-size: 14.5px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta { font-size: 12px; color: #7d8998; }
.item-del { flex: none; width: 44px; border: 0; background: transparent; color: #9aa6b3; font-size: 18px; cursor: pointer; border-radius: 0 10px 10px 0; }
.item-del:hover { color: #c2403c; }
</style>
