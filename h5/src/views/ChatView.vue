<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, showConfirmDialog, showFailToast } from 'vant'
import { AUTH_REQUIRED_EVENT, ApiError, confirmAgent, createAgentSession, getAgentSession, health } from '@/api/client'
import { useSettingsStore } from '@/api/settings'
import { KEYS } from '@/shared/storageKeys'
import { clock } from '@/shared/format'
import markUrl from '@/shared/mark.svg'
import { streamAgentMessage } from '@/api/sse'
import MarkdownView from '@/components/MarkdownView.vue'
import ToolGroup from '@/components/ToolGroup.vue'
import HistoryDrawer from '@/components/HistoryDrawer.vue'
import ChatHeader from '@/components/chat/ChatHeader.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import ChatWelcome from '@/components/chat/ChatWelcome.vue'
import PipelineCard from '@/components/chat/PipelineCard.vue'
import { followUps } from '@/components/chat/followUps'
import { allTools, applyEvent, findTool, toMessages, type Confirmation, type Message } from '@/components/chat/timeline'
import { t } from '@/i18n'

const messages = ref<Message[]>([])
const sessionId = ref(localStorage.getItem(KEYS.sessionId) || '')
const draft = ref('')
const busy = ref(false)
const loading = ref(false)
const showHistory = ref(false)
let controller: AbortController | null = null
const router = useRouter()
const settings = useSettingsStore()
// Server protects the API with GS_SERVER_API_KEY but this browser has none saved.
const needsKey = ref(false)
// Service status for the header dot: null while checking, false when /health fails.
const online = ref<boolean | null>(null)
async function checkHealth() {
  try {
    const result = await health()
    online.value = result.status === 'ok'
    needsKey.value = !!result.auth_required && !settings.apiKey
  } catch { online.value = false; needsKey.value = false }
}

// The window is the only scroll container. Follow new output only while the reader is at the bottom.
let stick = true
const atBottom = () => window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 80
const onWindowScroll = () => { stick = atBottom() }
const scroll = async (force = false) => {
  if (force) stick = true
  if (!stick) return
  await nextTick()
  window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'auto' })
}

async function createSession() {
  const session = await createAgentSession()
  sessionId.value = session.session_id
  localStorage.setItem(KEYS.sessionId, sessionId.value)
  messages.value = []
}
async function restore() {
  if (!sessionId.value) return
  loading.value = true
  try {
    const session = await getAgentSession(sessionId.value)
    messages.value = toMessages(session.messages, session.errors, session.confirmations)
    await scroll(true)
  } catch (e) {
    // The backend no longer has this session: quietly fall back to a fresh chat.
    if (e instanceof ApiError && Number(e.code) === 404) forgetSession()
    else showFailToast(e instanceof Error ? e.message : t('chat.restoreFailed'))
  } finally { loading.value = false }
}
function forgetSession() {
  sessionId.value = ''
  localStorage.removeItem(KEYS.sessionId)
  messages.value = []
}
async function openSession(id: string) {
  if (id === sessionId.value && messages.value.length) return
  sessionId.value = id
  localStorage.setItem(KEYS.sessionId, id)
  messages.value = []
  await restore()
}
function onSessionDeleted(id: string) { if (id === sessionId.value) forgetSession() }
async function newChatFromHistory() {
  try { await createSession() } catch (e) { showFailToast(e instanceof Error ? e.message : t('chat.createFailed')) }
}
async function newChat() {
  try {
    if (busy.value) return
    await showConfirmDialog({ title: t('chat.newConfirmTitle'), message: t('chat.newConfirmMessage') })
    await createSession()
  } catch (e) { if (e !== 'cancel') showFailToast(e instanceof Error ? e.message : t('chat.createFailed')) }
}
async function send(text?: string) {
  const content = (text ?? draft.value).trim()
  if (!content || busy.value) return
  if (needsKey.value) { window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT)); return }
  busy.value = true
  if (text === undefined) draft.value = ''
  try {
    if (!sessionId.value) await createSession()
    messages.value.push({ role: 'user', content, parts: [], at: Date.now() })
    messages.value.push({ role: 'assistant', content: '', parts: [], at: Date.now() })
    // Mutate the reactive proxy, not the raw object, so streamed deltas and confirm cards render live.
    const assistant = messages.value[messages.value.length - 1]
    await scroll(true)
    controller = new AbortController()
    await streamAgentMessage(sessionId.value, content, ev => {
      const error = applyEvent(ev, assistant)
      if (error) showFailToast(error)
      void scroll()
    }, controller.signal)
  } catch (e) {
    if (!(e instanceof DOMException && e.name === 'AbortError')) showFailToast(e instanceof Error ? e.message : t('chat.sendFailed'))
  } finally { busy.value = false; controller = null }
}
async function respond(item: Confirmation, approve: boolean) {
  if (item.pending || item.answered !== undefined) return
  item.pending = true
  try {
    await confirmAgent(sessionId.value, item.confirmId, approve)
    item.answered = approve
    if (!approve) {
      const reply = messages.value.find(m => m.parts.some(p => p.kind === 'confirm' && p.confirm === item))
      const tool = reply && findTool(reply, item.toolId)
      if (tool) tool.rejected = true
    }
  } catch (e) { showFailToast(e instanceof Error ? e.message : t('chat.confirmFailed')) }
  finally { item.pending = false }
}
const isStreaming = (index: number) => busy.value && index === messages.value.length - 1
const lastIndex = computed(() => messages.value.length - 1)
// Retry re-sends the user message this reply answered (as a new turn in the same session).
function questionBefore(index: number): string | undefined {
  for (let i = index - 1; i >= 0; i--) if (messages.value[i].role === 'user') return messages.value[i].content
}
const chips = computed(() => {
  const last = messages.value[lastIndex.value]
  return last?.role === 'assistant' && !busy.value ? followUps(allTools(last)) : []
})
function clearLocal() { controller?.abort(); busy.value = false; sessionId.value = ''; messages.value = [] }
onMounted(() => {
  window.addEventListener('saodi:clear-chat', clearLocal)
  window.addEventListener('scroll', onWindowScroll, { passive: true })
  void checkHealth(); void restore()
})
onUnmounted(() => {
  window.removeEventListener('saodi:clear-chat', clearLocal)
  window.removeEventListener('scroll', onWindowScroll)
  controller?.abort()
})
</script>

<template>
  <div class="chat-page">
    <div class="chat-top"><div class="col"><ChatHeader :busy="busy" :online="online" @history="showHistory = true" @new="newChat" /></div></div>
    <HistoryDrawer v-model:show="showHistory" :current-id="sessionId" :busy="busy" @select="openSession" @deleted="onSessionDeleted" @new="newChatFromHistory" />
    <div class="col message-list">
      <div v-if="needsKey" class="auth-notice"><span>{{ t('auth.message') }}</span><Button size="small" type="primary" @click="router.push('/settings')">{{ t('auth.goSettings') }}</Button></div>
      <div v-if="loading" class="empty">{{ t('chat.loading') }}</div>
      <ChatWelcome v-else-if="!messages.length" @ask="send" />
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
        <template v-if="message.role === 'user'">
          <div class="bubble">{{ message.content }}</div>
          <time v-if="message.at" class="stamp">{{ clock(new Date(message.at)) }}</time>
        </template>
        <template v-else>
          <div class="who"><img :src="markUrl" alt="" class="avatar"><strong>{{ t('brand.name') }}</strong><time v-if="message.at" class="stamp">{{ clock(new Date(message.at)) }}</time></div>
          <div class="reply">
            <template v-for="(part, i) in message.parts" :key="i">
              <div v-if="part.kind === 'text'" class="text-card"><MarkdownView :text="part.text" /></div>
              <ToolGroup v-else-if="part.kind === 'tools'" :tools="part.tools" />
              <div v-else-if="part.kind === 'error'" class="error-line">{{ t('chat.errorLine', { message: part.message }) }}</div>
              <PipelineCard v-else :confirm="part.confirm" :tool="findTool(message, part.confirm.toolId)" :follow-ups="allTools(message)" @respond="approve => respond(part.confirm, approve)" />
            </template>
            <span v-if="isStreaming(index) && message.parts[message.parts.length - 1]?.kind !== 'text'" class="thinking"><i /><i /><i />{{ t('chat.thinking') }}</span>
            <div v-if="index === lastIndex && !busy && questionBefore(index)" class="reply-actions">
              <button type="button" class="ghost-btn" @click="send(questionBefore(index))">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4h4" /></svg>{{ t('common.retry') }}
              </button>
            </div>
          </div>
        </template>
      </div>
      <div v-if="chips.length" class="chips" :aria-label="t('chat.followUpsAria')">
        <button v-for="chip in chips" :key="chip" type="button" class="chip" @click="send(chip)">{{ chip }}</button>
      </div>
    </div>
    <div class="composer-dock"><div class="col"><ChatComposer v-model="draft" :disabled="busy || loading" @send="send()" /></div></div>
  </div>
</template>

<style scoped>
/* One reading column shared by header, messages and composer; the window is the only scroller. */
.chat-page { --col: 728px; --gutter: 14px; --tabbar: 56px; min-height: calc(100dvh - var(--tabbar) - env(safe-area-inset-bottom)); display: flex; flex-direction: column; background: var(--sd-bg-grad); }
.col { width: 100%; max-width: calc(var(--col) + 2 * var(--gutter)); margin: 0 auto; padding-left: var(--gutter); padding-right: var(--gutter); }
.chat-top { position: sticky; top: 0; z-index: 10; background: color-mix(in srgb, var(--sd-primary-softer) 88%, transparent); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--sd-line); }
.message-list { flex: 1; padding-top: 16px; padding-bottom: 16px; }
.message { display: flex; flex-direction: column; margin-bottom: 20px; }
.message.user { align-items: flex-end; }
.bubble { max-width: min(85%, 620px); border-radius: var(--sd-r-lg) var(--sd-r-lg) var(--sd-r-xs) var(--sd-r-lg); padding: 10px 14px; background: var(--sd-primary-soft); color: var(--sd-ink); box-shadow: inset 0 0 0 1px var(--sd-primary-line); font-size: var(--sd-fs-md); line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere; }
.stamp { margin-top: 4px; font-size: var(--sd-fs-2xs); color: var(--sd-faint); font-variant-numeric: tabular-nums; }
.who { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.who strong { font-size: var(--sd-fs-sm); color: var(--sd-ink); }
.who .stamp { margin-top: 0; }
.avatar { width: 30px; height: 30px; padding: 3px; border-radius: 50%; background: var(--sd-surface); box-shadow: var(--sd-shadow-1); }
.reply { width: 100%; min-width: 0; display: flex; flex-direction: column; gap: 10px; }
.text-card { padding: 14px 16px; border-radius: var(--sd-r-lg); background: var(--sd-surface); box-shadow: var(--sd-shadow-1); color: var(--sd-ink); }
.thinking { display: inline-flex; align-items: center; gap: 4px; padding: 2px 0; color: var(--sd-muted); font-size: var(--sd-fs-sm); }
.thinking i { width: 5px; height: 5px; border-radius: 50%; background: var(--sd-primary); animation: blink 1.2s infinite ease-in-out; }
.thinking i:nth-child(2) { animation-delay: .15s; }
.thinking i:nth-child(3) { animation-delay: .3s; margin-right: 4px; }
@keyframes blink { 0%, 80%, 100% { opacity: .25; } 40% { opacity: 1; } }
.reply-actions { display: flex; justify-content: flex-end; }
.ghost-btn { display: inline-flex; align-items: center; gap: 4px; height: 28px; padding: 0 10px; border: 0; border-radius: var(--sd-r-pill); background: transparent; color: var(--sd-muted); font-size: var(--sd-fs-xs); cursor: pointer; }
.ghost-btn:hover { background: var(--sd-surface); color: var(--sd-primary); }
.ghost-btn svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: -4px; }
.chip { max-width: 100%; padding: 8px 14px; border: 1px solid var(--sd-primary-line); border-radius: var(--sd-r-pill); background: var(--sd-surface); color: var(--sd-primary-strong); font-size: var(--sd-fs-sm); line-height: 1.3; text-align: left; cursor: pointer; box-shadow: var(--sd-shadow-1); }
.chip:active { background: var(--sd-primary-soft); }
.auth-notice { display: flex; align-items: center; justify-content: space-between; gap: 10px; background: var(--sd-warning-soft); border: 1px solid var(--sd-warning-line); border-radius: var(--sd-r-md); padding: 10px 12px; margin-bottom: 14px; font-size: var(--sd-fs-sm); }
.error-line { padding: 9px 12px; border-radius: var(--sd-r-md); background: var(--sd-danger-soft); color: var(--sd-danger); font-size: var(--sd-fs-sm); overflow-wrap: anywhere; }
.composer-dock { position: sticky; bottom: calc(var(--tabbar) + env(safe-area-inset-bottom)); z-index: 10; padding: 8px 0 10px; background: linear-gradient(180deg, transparent, var(--sd-bg) 30%); }
</style>
