<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Button, showConfirmDialog, showFailToast } from 'vant'
import { ApiError, confirmAgent, createAgentSession, getAgentSession } from '@/api/client'
import { streamAgentMessage, type AgentEvent } from '@/api/sse'
import MarkdownLite from '@/components/MarkdownLite.vue'
import ToolCallCard from '@/components/ToolCallCard.vue'

type Tool = { id: string; name: string; input: unknown; output?: unknown; isError?: boolean }
type Confirmation = { confirmId: string; summary: string; name: string; input: unknown; pending: boolean; answered?: boolean }
type Message = { role: 'user' | 'assistant'; content: string; tools: Tool[]; confirms: Confirmation[] }
const messages = ref<Message[]>([])
const sessionId = ref(localStorage.getItem('pi.sessionId') || '')
const draft = ref('')
const busy = ref(false)
const loading = ref(false)
const scroller = ref<HTMLElement | null>(null)
let controller: AbortController | null = null
const scroll = async () => { await nextTick(); scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' }) }
async function createSession() {
  const session = await createAgentSession()
  sessionId.value = session.session_id
  localStorage.setItem('pi.sessionId', sessionId.value)
  messages.value = []
}
async function restore() {
  if (!sessionId.value) return
  loading.value = true
  try {
    const session = await getAgentSession(sessionId.value)
    messages.value = session.messages.filter(m => m.role === 'user' || m.role === 'assistant').map(m => ({
      role: m.role as Message['role'], content: typeof m.content === 'string' ? m.content : Array.isArray(m.content) ? m.content.map((part: unknown) => typeof part === 'object' && part !== null && 'text' in part ? String(part.text) : '').join('\n') : '', tools: [], confirms: [],
    }))
    await scroll()
  } catch (e) {
    if (e instanceof ApiError && e.code === 404) {
      sessionId.value = ''
      localStorage.removeItem('pi.sessionId')
    } else showFailToast(e instanceof Error ? e.message : '恢复对话失败')
  } finally { loading.value = false }
}
async function newChat() {
  try {
    if (busy.value) return
    await showConfirmDialog({ title: '新对话', message: '创建新对话并切换？' })
    await createSession()
  } catch (e) { if (e !== 'cancel') showFailToast(e instanceof Error ? e.message : '新建失败') }
}
function handleEvent(ev: AgentEvent, message: Message) {
  switch (ev.type) {
    case 'text_delta': message.content += ev.text; break
    case 'tool_call': message.tools.push({ id: ev.id, name: ev.name, input: ev.input }); break
    case 'tool_result': {
      const tool = message.tools.find(item => item.id === ev.id)
      if (tool) { tool.output = ev.output; tool.isError = ev.is_error }
      break
    }
    case 'confirm_required': message.confirms.push({ confirmId: ev.confirm_id, name: ev.name, input: ev.input, summary: ev.summary, pending: false }); break
    case 'error': showFailToast(ev.message); break
    case 'done': break
  }
  void scroll()
}
async function send() {
  const content = draft.value.trim()
  if (!content || busy.value) return
  busy.value = true
  draft.value = ''
  try {
    if (!sessionId.value) await createSession()
    messages.value.push({ role: 'user', content, tools: [], confirms: [] })
    messages.value.push({ role: 'assistant', content: '', tools: [], confirms: [] })
    // Mutate the reactive proxy, not the raw object, so streamed deltas and confirm cards render live.
    const assistant = messages.value[messages.value.length - 1]
    await scroll()
    controller = new AbortController()
    await streamAgentMessage(sessionId.value, content, ev => handleEvent(ev, assistant), controller.signal)
  } catch (e) {
    if (!(e instanceof DOMException && e.name === 'AbortError')) showFailToast(e instanceof Error ? e.message : '发送失败')
  } finally { busy.value = false; controller = null }
}
async function respond(item: Confirmation, approve: boolean) {
  if (item.pending || item.answered) return
  item.pending = true
  try {
    await confirmAgent(sessionId.value, item.confirmId, approve)
    item.answered = approve
  } catch (e) { showFailToast(e instanceof Error ? e.message : '确认失败') }
  finally { item.pending = false }
}
function clearLocal() { controller?.abort(); busy.value = false; sessionId.value = ''; messages.value = [] }
onMounted(() => { window.addEventListener('pi:clear-chat', clearLocal); void restore() })
onUnmounted(() => { window.removeEventListener('pi:clear-chat', clearLocal); controller?.abort() })
</script>

<template>
  <div class="page chat-page">
    <header class="page-header"><span>Pi Agent</span><Button size="small" plain type="primary" :disabled="busy" @click="newChat">新对话</Button></header>
    <div ref="scroller" class="message-list">
      <div v-if="loading" class="empty">正在加载对话…</div>
      <div v-else-if="!messages.length" class="empty">你好，我是 Pi Agent。可以查询机器人状态、任务和报告。</div>
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
        <div class="bubble">
          <MarkdownLite v-if="message.content" :text="message.content" />
          <span v-else-if="message.role === 'assistant' && busy" class="muted">正在思考…</span>
          <ToolCallCard v-for="tool in message.tools" :key="tool.id" :name="tool.name" :input="tool.input" :output="tool.output" :is-error="tool.isError" />
          <div v-for="confirm in message.confirms" :key="confirm.confirmId" class="confirm-card">
            <strong>待确认 · {{ confirm.name }}</strong><p>{{ confirm.summary }}</p>
            <ToolCallCard :name="confirm.name" :input="confirm.input" />
            <div v-if="confirm.answered !== undefined" class="muted">{{ confirm.answered ? '已确认执行' : '已取消' }}</div>
            <div v-else class="row"><Button size="small" type="primary" :loading="confirm.pending" @click="respond(confirm, true)">确认执行</Button><Button size="small" :disabled="confirm.pending" @click="respond(confirm, false)">取消</Button></div>
          </div>
        </div>
      </div>
    </div>
    <form class="composer" @submit.prevent="send">
      <textarea v-model="draft" rows="1" placeholder="问问 Pi Agent…" aria-label="消息内容" @keydown.enter.exact.prevent="send" />
      <Button type="primary" size="small" native-type="submit" :disabled="busy || loading || !draft.trim()">发送</Button>
    </form>
  </div>
</template>

<style scoped>
.chat-page { height: calc(100dvh - 58px - env(safe-area-inset-bottom)); display: flex; flex-direction: column; }
.message-list { flex: 1; min-height: 0; overflow-y: auto; padding: 15px; }
.message { display: flex; margin-bottom: 14px; }
.message.user { justify-content: flex-end; }
.bubble { max-width: 90%; border-radius: 14px; padding: 12px 14px; background: #fff; font-size: 14px; line-height: 1.55; min-width: 45px; }
.user .bubble { background: #d9edff; }
.confirm-card { background: #fff8e9; border: 1px solid #f1d6a3; border-radius: 10px; padding: 12px; margin-top: 10px; }
.confirm-card p { margin: 8px 0; }
.confirm-card .row { margin-top: 10px; }
.composer { background: #fff; display: flex; align-items: end; gap: 9px; padding: 10px 12px calc(10px + env(safe-area-inset-bottom)); border-top: 1px solid #ebeff3; }
.composer textarea { resize: none; flex: 1; max-height: 110px; min-height: 38px; border: 1px solid #e0e8f2; border-radius: 10px; padding: 9px; }
</style>
