<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Icon, showConfirmDialog, showFailToast } from 'vant'
import { AUTH_REQUIRED_EVENT, ApiError, confirmAgent, createAgentSession, getAgentSession, health, type SessionError } from '@/api/client'
import { useSettingsStore } from '@/stores/settings'
import { KEYS } from '@/storageKeys'
import { streamAgentMessage, type AgentEvent } from '@/api/sse'
import MarkdownView from '@/components/MarkdownView.vue'
import ToolCallCard from '@/components/ToolCallCard.vue'
import ToolGroup, { type ToolItem } from '@/components/ToolGroup.vue'
import HistoryDrawer from '@/components/HistoryDrawer.vue'
import { t } from '@/i18n'

type Confirmation = { confirmId: string; summary: string; name: string; input: unknown; pending: boolean; answered?: boolean }
// One assistant reply is a timeline in event order: text runs, groups of consecutive tool calls, confirm cards.
type Part =
  | { kind: 'text'; text: string }
  | { kind: 'tools'; tools: ToolItem[] }
  | { kind: 'confirm'; confirm: Confirmation }
  | { kind: 'error'; message: string }
type Message = { role: 'user' | 'assistant'; content: string; parts: Part[] }
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
async function checkAuth() {
  try { needsKey.value = !!(await health()).auth_required && !settings.apiKey } catch { needsKey.value = false }
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

type Block = { type?: string; text?: string; id?: string; name?: string; input?: unknown; tool_use_id?: string; content?: unknown; is_error?: boolean }
const parseOutput = (value: unknown) => { if (typeof value !== 'string') return value; try { return JSON.parse(value) } catch { return value } }
// Rebuild timelines from the stored transcript: consecutive assistant turns merge into one reply,
// and tool_result blocks (stored as user turns) fill in the matching tool call.
// Persisted SSE errors go back where they happened: after the first `after_message` stored messages.
function toMessages(stored: { role: string; content: unknown }[], errors: SessionError[] = []): Message[] {
  const result: Message[] = []
  const tools = new Map<string, ToolItem>()
  const pending = [...errors].sort((a, b) => a.after_message - b.after_message)
  const flushErrors = (upTo: number) => {
    while (pending.length && pending[0].after_message <= upTo) {
      let reply = result[result.length - 1]
      if (reply?.role !== 'assistant') { reply = { role: 'assistant', content: '', parts: [] }; result.push(reply) }
      reply.parts.push({ kind: 'error', message: pending.shift()!.message })
    }
  }
  for (const [index, m] of stored.entries()) {
    flushErrors(index)
    const blocks: Block[] = typeof m.content === 'string' ? [{ type: 'text', text: m.content }] : Array.isArray(m.content) ? m.content as Block[] : []
    if (m.role === 'user' && blocks.some(b => b.type === 'tool_result')) {
      for (const b of blocks) {
        const tool = b.tool_use_id ? tools.get(b.tool_use_id) : undefined
        if (tool) { tool.output = parseOutput(b.content); tool.isError = !!b.is_error }
      }
      continue
    }
    if (m.role === 'user') {
      result.push({ role: 'user', content: blocks.map(b => b.text ?? '').join('\n'), parts: [] })
      continue
    }
    if (m.role !== 'assistant') continue
    let reply = result[result.length - 1]
    if (reply?.role !== 'assistant') { reply = { role: 'assistant', content: '', parts: [] }; result.push(reply) }
    for (const b of blocks) {
      if (b.type === 'text' && b.text) appendText(reply, b.text)
      else if (b.type === 'tool_use' && b.id) {
        const tool: ToolItem = { id: b.id, name: b.name ?? '', input: b.input ?? {} }
        tools.set(tool.id, tool)
        appendTool(reply, tool)
      }
    }
  }
  flushErrors(Number.MAX_SAFE_INTEGER)
  return result
}
async function restore() {
  if (!sessionId.value) return
  loading.value = true
  try {
    const session = await getAgentSession(sessionId.value)
    messages.value = toMessages(session.messages, session.errors)
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
function appendText(message: Message, text: string) {
  const last = message.parts[message.parts.length - 1]
  if (last?.kind === 'text') last.text += text
  else message.parts.push({ kind: 'text', text })
}
function appendTool(message: Message, tool: ToolItem) {
  const last = message.parts[message.parts.length - 1]
  if (last?.kind === 'tools') last.tools.push(tool)
  else message.parts.push({ kind: 'tools', tools: [tool] })
}
function findTool(message: Message, id: string) {
  for (const part of message.parts) if (part.kind === 'tools') { const tool = part.tools.find(t => t.id === id); if (tool) return tool }
}
function handleEvent(ev: AgentEvent, message: Message) {
  switch (ev.type) {
    case 'text_delta': appendText(message, ev.text); break
    case 'tool_call': appendTool(message, { id: ev.id, name: ev.name, input: ev.input }); break
    case 'tool_result': {
      const tool = findTool(message, ev.id)
      if (tool) { tool.output = ev.output; tool.isError = ev.is_error }
      break
    }
    case 'confirm_required': message.parts.push({ kind: 'confirm', confirm: { confirmId: ev.confirm_id, name: ev.name, input: ev.input, summary: ev.summary, pending: false } }); break
    case 'error': message.parts.push({ kind: 'error', message: ev.message }); showFailToast(ev.message); break
    case 'done': break
  }
  void scroll()
}
async function send() {
  const content = draft.value.trim()
  if (!content || busy.value) return
  if (needsKey.value) { window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT)); return }
  busy.value = true
  draft.value = ''
  try {
    if (!sessionId.value) await createSession()
    messages.value.push({ role: 'user', content, parts: [] })
    messages.value.push({ role: 'assistant', content: '', parts: [] })
    // Mutate the reactive proxy, not the raw object, so streamed deltas and confirm cards render live.
    const assistant = messages.value[messages.value.length - 1]
    await scroll(true)
    controller = new AbortController()
    await streamAgentMessage(sessionId.value, content, ev => handleEvent(ev, assistant), controller.signal)
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
  } catch (e) { showFailToast(e instanceof Error ? e.message : t('chat.confirmFailed')) }
  finally { item.pending = false }
}
const isStreaming = (index: number) => busy.value && index === messages.value.length - 1
function clearLocal() { controller?.abort(); busy.value = false; sessionId.value = ''; messages.value = [] }
onMounted(() => {
  window.addEventListener('saodi:clear-chat', clearLocal)
  window.addEventListener('scroll', onWindowScroll, { passive: true })
  void checkAuth(); void restore()
})
onUnmounted(() => {
  window.removeEventListener('saodi:clear-chat', clearLocal)
  window.removeEventListener('scroll', onWindowScroll)
  controller?.abort()
})
</script>

<template>
  <div class="chat-page">
    <header class="chat-header"><div class="col page-header"><div class="head-left"><button type="button" class="history-btn" :aria-label="t('chat.historyAria')" @click="showHistory = true"><Icon name="bars" /><span>{{ t('chat.history') }}</span></button><span class="brand">{{ t('brand.name') }}<small v-if="t('brand.sub')">{{ t('brand.sub') }}</small></span></div><Button size="small" plain type="primary" :disabled="busy" @click="newChat">{{ t('chat.new') }}</Button></div></header>
    <HistoryDrawer v-model:show="showHistory" :current-id="sessionId" :busy="busy" @select="openSession" @deleted="onSessionDeleted" @new="newChatFromHistory" />
    <div class="col message-list">
      <div v-if="needsKey" class="auth-notice"><span>{{ t('auth.message') }}</span><Button size="small" type="primary" @click="router.push('/settings')">{{ t('auth.goSettings') }}</Button></div>
      <div v-if="loading" class="empty">{{ t('chat.loading') }}</div>
      <div v-else-if="!messages.length" class="empty">{{ t('chat.welcome') }}</div>
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
        <div v-if="message.role === 'user'" class="bubble">{{ message.content }}</div>
        <div v-else class="reply">
          <template v-for="(part, i) in message.parts" :key="i">
            <MarkdownView v-if="part.kind === 'text'" :text="part.text" />
            <ToolGroup v-else-if="part.kind === 'tools'" :tools="part.tools" />
            <div v-else-if="part.kind === 'error'" class="error-line">{{ t('chat.errorLine', { message: part.message }) }}</div>
            <div v-else class="confirm-card">
              <strong>{{ t('chat.confirmTitle', { name: part.confirm.name }) }}</strong><p>{{ part.confirm.summary }}</p>
              <ToolCallCard :name="part.confirm.name" :input="part.confirm.input" />
              <div v-if="part.confirm.answered !== undefined" class="muted">{{ part.confirm.answered ? t('chat.confirmed') : t('chat.cancelled') }}</div>
              <div v-else class="row"><Button size="small" type="primary" :loading="part.confirm.pending" @click="respond(part.confirm, true)">{{ t('chat.approve') }}</Button><Button size="small" :disabled="part.confirm.pending" @click="respond(part.confirm, false)">{{ t('chat.reject') }}</Button></div>
            </div>
          </template>
          <span v-if="isStreaming(index) && message.parts[message.parts.length - 1]?.kind !== 'text'" class="muted thinking">{{ t('chat.thinking') }}</span>
        </div>
      </div>
    </div>
    <div class="composer-dock">
      <form class="col composer" @submit.prevent="send">
        <textarea v-model="draft" rows="1" :placeholder="t('chat.placeholder')" :aria-label="t('chat.inputAria')" @keydown.enter.exact.prevent="send" />
        <Button type="primary" size="small" native-type="submit" :disabled="busy || loading || !draft.trim()">{{ t('chat.send') }}</Button>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* One reading column shared by header, messages and composer; the window is the only scroller. */
.chat-page { --col: 728px; --gutter: 16px; --tabbar: 50px; min-height: calc(100dvh - 58px - env(safe-area-inset-bottom)); display: flex; flex-direction: column; margin-bottom: calc(var(--tabbar) - 58px); }
.col { width: 100%; max-width: calc(var(--col) + 2 * var(--gutter)); margin: 0 auto; padding-left: var(--gutter); padding-right: var(--gutter); }
.chat-header { position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid #e8eef5; }
.chat-header .page-header { background: transparent; }
.head-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.history-btn { display: inline-flex; align-items: center; gap: 4px; height: 32px; padding: 0 10px 0 8px; border: 1px solid #d8e2ee; border-radius: 16px; background: #fff; color: #33506e; font-size: 13px; font-weight: 600; cursor: pointer; }
.history-btn .van-icon { font-size: 16px; }
.brand { display: inline-flex; align-items: baseline; gap: 6px; }
.brand small { font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: #7d8998; }
.message-list { flex: 1; padding-top: 18px; padding-bottom: 18px; }
.message { display: flex; margin-bottom: 20px; }
.message.user { justify-content: flex-end; }
.bubble { max-width: min(85%, 620px); border-radius: 16px 16px 4px 16px; padding: 9px 14px; background: #d9edff; font-size: 15px; line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere; }
.reply { width: 100%; min-width: 0; display: flex; flex-direction: column; gap: 10px; }
.thinking { padding: 2px 0; }
.auth-notice { display: flex; align-items: center; justify-content: space-between; gap: 10px; background: #fff8e9; border: 1px solid #f1d6a3; border-radius: 10px; padding: 10px 12px; margin-bottom: 14px; font-size: 13px; }
.confirm-card { background: #fff8e9; border: 1px solid #f1d6a3; border-radius: 10px; padding: 12px; font-size: 14px; }
.error-line { padding: 8px 12px; border-radius: 10px; background: #fdeeee; color: #b23b37; font-size: 13.5px; overflow-wrap: anywhere; }
.confirm-card p { margin: 8px 0; overflow-wrap: anywhere; }
.confirm-card .row { margin-top: 10px; }
.confirm-card :deep(.dot) { display: none; }
.composer-dock { position: sticky; bottom: calc(var(--tabbar) + env(safe-area-inset-bottom)); z-index: 10; background: #f4f7fb; padding-bottom: 10px; }
.composer { display: flex; align-items: end; gap: 9px; }
.composer textarea { resize: none; flex: 1; max-height: 110px; min-height: 42px; border: 1px solid #d8e2ee; border-radius: 12px; padding: 10px 12px; line-height: 20px; background: #fff; box-shadow: 0 2px 10px #173a630d; }
.composer :deep(.van-button) { height: 42px; padding: 0 16px; border-radius: 12px; }
</style>
