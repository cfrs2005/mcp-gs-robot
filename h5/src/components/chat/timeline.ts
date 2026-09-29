import { messageForCode, type SessionError } from '@/api/client'
import type { AgentEvent } from '@/api/sse'
import type { ToolItem } from '@/components/ToolGroup.vue'

// One assistant reply is a timeline in event order: text runs, groups of consecutive tool calls, confirm cards.
// Live SSE events (applyEvent) and stored transcripts (toMessages) build the same structure.
export type Confirmation = {
  confirmId: string; summary: string; name: string; input: unknown; pending: boolean; answered?: boolean
  /** The tool_call this confirmation gates (same reply, same name and input). */
  toolId?: string
}
export type Part =
  | { kind: 'text'; text: string }
  | { kind: 'tools'; tools: ToolItem[] }
  | { kind: 'confirm'; confirm: Confirmation }
  | { kind: 'error'; message: string }
/** `at` (ms) exists only for messages created live in this tab; stored transcripts carry no time. */
export type Message = { role: 'user' | 'assistant'; content: string; parts: Part[]; at?: number }

export function appendText(message: Message, text: string) {
  const last = message.parts[message.parts.length - 1]
  if (last?.kind === 'text') last.text += text
  else message.parts.push({ kind: 'text', text })
}
export function appendTool(message: Message, tool: ToolItem) {
  const last = message.parts[message.parts.length - 1]
  if (last?.kind === 'tools') last.tools.push(tool)
  else message.parts.push({ kind: 'tools', tools: [tool] })
}
export function allTools(message: Message): ToolItem[] {
  return message.parts.flatMap(part => part.kind === 'tools' ? part.tools : [])
}
export function findTool(message: Message, id: string | undefined): ToolItem | undefined {
  return id === undefined ? undefined : allTools(message).find(tool => tool.id === id)
}

function linkConfirm(message: Message, name: string, input: unknown): string | undefined {
  const linked = new Set(message.parts.flatMap(p => p.kind === 'confirm' && p.confirm.toolId ? [p.confirm.toolId] : []))
  const key = JSON.stringify(input)
  return allTools(message).find(tool => tool.name === name && !linked.has(tool.id) && JSON.stringify(tool.input) === key)?.id
}

/** Apply one SSE event; returns the localized error text for `error` events (the caller toasts it). */
export function applyEvent(ev: AgentEvent, message: Message): string | undefined {
  switch (ev.type) {
    case 'text_delta': appendText(message, ev.text); break
    case 'tool_call': appendTool(message, { id: ev.id, name: ev.name, input: ev.input }); break
    case 'tool_result': {
      const tool = findTool(message, ev.id)
      if (tool) { tool.output = ev.output; tool.isError = ev.is_error }
      break
    }
    case 'confirm_required':
      message.parts.push({ kind: 'confirm', confirm: { confirmId: ev.confirm_id, name: ev.name, input: ev.input, summary: ev.summary, pending: false, toolId: linkConfirm(message, ev.name, ev.input) } })
      break
    case 'error': { const text = messageForCode(ev.code, ev.message); message.parts.push({ kind: 'error', message: text }); return text }
    case 'done': break
  }
}

type Block = { type?: string; text?: string; id?: string; name?: string; input?: unknown; tool_use_id?: string; content?: unknown; is_error?: boolean }
const parseOutput = (value: unknown) => { if (typeof value !== 'string') return value; try { return JSON.parse(value) } catch { return value } }

// Rebuild timelines from the stored transcript: consecutive assistant turns merge into one reply,
// and tool_result blocks (stored as user turns) fill in the matching tool call.
// Persisted SSE errors go back where they happened: after the first `after_message` stored messages.
export function toMessages(stored: { role: string; content: unknown }[], errors: SessionError[] = []): Message[] {
  const result: Message[] = []
  const tools = new Map<string, ToolItem>()
  const pending = [...errors].sort((a, b) => a.after_message - b.after_message)
  const flushErrors = (upTo: number) => {
    while (pending.length && pending[0].after_message <= upTo) {
      let reply = result[result.length - 1]
      if (reply?.role !== 'assistant') { reply = { role: 'assistant', content: '', parts: [] }; result.push(reply) }
      const error = pending.shift()!
      reply.parts.push({ kind: 'error', message: messageForCode(error.code, error.message) })
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
