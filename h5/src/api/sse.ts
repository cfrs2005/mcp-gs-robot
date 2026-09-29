import { apiHeaders, apiUrl, parseResponse } from './client'
import { t } from '@/i18n'

export type AgentEvent =
  | { type: 'text_delta'; text: string }
  | { type: 'tool_call'; id: string; name: string; input: Record<string, unknown> }
  | { type: 'tool_result'; id: string; name: string; output: unknown; is_error: boolean }
  | { type: 'confirm_required'; confirm_id: string; tool_use_id?: string; name: string; input: Record<string, unknown>; summary: string }
  | { type: 'done'; message_id: string; usage: Record<string, unknown> }
  | { type: 'error'; message: string; code?: string }

export async function streamAgentMessage(
  sessionId: string,
  content: string,
  onEvent: (ev: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const headers = apiHeaders()
  headers.set('Content-Type', 'application/json')
  const response = await fetch(apiUrl(`/api/v1/agent/sessions/${encodeURIComponent(sessionId)}/messages`), {
    method: 'POST', headers, body: JSON.stringify({ content }), signal,
  })
  if (!response.ok) await parseResponse(response)
  if (!response.body) throw new Error(t('errors.noStream'))

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  const consume = (line: string) => {
    if (!line.startsWith('data:')) return
    const data = line.slice(5).trim()
    if (data && data !== '[DONE]') onEvent(JSON.parse(data) as AgentEvent)
  }
  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) consume(line.replace(/\r$/, ''))
    }
    buffer += decoder.decode()
    if (buffer) consume(buffer.replace(/\r$/, ''))
  } finally {
    reader.releaseLock()
  }
}
