import type { Component } from 'vue'
import RobotStatusCard from './RobotStatusCard.vue'
import ReportsCard from './ReportsCard.vue'
import MapImageCard from './MapImageCard.vue'

// The one table of tool name → result card. ToolGroup shows the card for a successful result that
// `accepts` it; everything else (no entry, error, unexpected shape) keeps the plain tool row.
// Cards receive { input, output, name } and must render defensively: output shapes come from upstream.
type CardSpec = { component: Component; accepts: (output: unknown) => boolean }

const obj = (v: unknown): Record<string, unknown> | null => v && typeof v === 'object' && !Array.isArray(v) ? v as Record<string, unknown> : null
const nonEmpty = (v: unknown) => Array.isArray(v) && v.length > 0

const RESULT_CARDS: Record<string, CardSpec> = {
  get_robot_status: { component: RobotStatusCard, accepts: out => nonEmpty(obj(out)?.list) },
  list_task_reports: { component: ReportsCard, accepts: out => nonEmpty(obj(out)?.robotTaskReports) },
  get_map_canvas: { component: MapImageCard, accepts: out => !!obj(obj(out)?.mapPng) },
  get_task_report_map_images: { component: MapImageCard, accepts: out => nonEmpty(obj(out)?.list) },
}

const TRUNCATED = '…[truncated]'

/** The server cuts tool results over 20k characters and appends "…[truncated]" (agent/core.py), which
 *  happens to a 20-row report page. The stored transcript then holds that string JSON-encoded and cut
 *  again. Unwrap the string layers, then keep the complete leading array elements: scan the JSON,
 *  remember the last point where an object inside an array closed (preferring the shallowest array, so
 *  no row is cut mid-way), cut there and close the open brackets. */
function unwrap(text: string, cut = false): { text: string; cut: boolean } {
  if (text.endsWith(TRUNCATED)) return unwrap(text.slice(0, -TRUNCATED.length), true)
  if (text.startsWith('"')) {
    // A JSON string literal, possibly missing its end (and cut inside an escape sequence).
    for (let drop = 0; drop <= 6; drop++) {
      try {
        const inner: unknown = JSON.parse(`${text.slice(0, text.length - drop)}${text.endsWith('"') && drop === 0 ? '' : '"'}`)
        if (typeof inner === 'string') return unwrap(inner, cut || drop > 0 || !text.endsWith('"'))
      } catch { /* try a shorter prefix */ }
    }
  }
  return { text, cut }
}

export function salvageJson(raw: string): unknown {
  const { text: body, cut } = unwrap(raw)
  if (!cut) { try { return JSON.parse(body) } catch { return undefined } }
  const stack: string[] = []
  const cuts = new Map<number, { at: number; closers: string }>()
  let inString = false, escaped = false
  for (let i = 0; i < body.length; i++) {
    const c = body[i]
    if (inString) {
      if (escaped) escaped = false
      else if (c === '\\') escaped = true
      else if (c === '"') inString = false
      continue
    }
    if (c === '"') inString = true
    else if (c === '{' || c === '[') stack.push(c)
    else if (c === '}' || c === ']') {
      stack.pop()
      if (c === '}' && stack[stack.length - 1] === '[') {
        cuts.set(stack.length, { at: i + 1, closers: [...stack].reverse().map(b => b === '[' ? ']' : '}').join('') })
      }
    }
  }
  if (!cuts.size) return undefined
  const best = cuts.get(Math.min(...cuts.keys()))!
  try { return JSON.parse(body.slice(0, best.at) + best.closers) } catch { return undefined }
}

export type CardView = { component: Component; output: unknown; truncated: boolean }

export function resultCard(tool: { name: string; output?: unknown; isError?: boolean }): CardView | null {
  if (tool.output === undefined || tool.isError) return null
  const spec = RESULT_CARDS[tool.name]
  if (!spec) return null
  if (spec.accepts(tool.output)) return { component: spec.component, output: tool.output, truncated: false }
  const salvaged = typeof tool.output === 'string' ? salvageJson(tool.output) : undefined
  return salvaged !== undefined && spec.accepts(salvaged) ? { component: spec.component, output: salvaged, truncated: true } : null
}
