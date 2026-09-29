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

/** Server-side truncation note (docs/ARCHITECTURE_V3.md §4 "工具结果截断"): the first `_truncated` found. */
export type Truncation = { field: string; kept: number; total: number; unit: 'items' | 'chars' }
export function truncationOf(value: unknown, depth = 0): Truncation | null {
  if (!value || typeof value !== 'object' || depth > 4) return null
  const note = (value as { _truncated?: unknown })._truncated as Partial<Truncation> | undefined
  if (note && typeof note.kept === 'number' && typeof note.total === 'number') {
    return { field: String(note.field ?? ''), kept: note.kept, total: note.total, unit: note.unit === 'chars' ? 'chars' : 'items' }
  }
  for (const child of Object.values(value)) {
    const found = truncationOf(child, depth + 1)
    if (found) return found
  }
  return null
}

export type CardView = { component: Component; output: unknown; truncation: Truncation | null }

// Sessions saved before structured truncation hold a cut, doubly encoded string ("…[truncated]").
// It no longer parses, so it simply gets no card and stays readable as raw text in the tool row.
export function resultCard(tool: { name: string; output?: unknown; isError?: boolean }): CardView | null {
  if (tool.output === undefined || tool.isError) return null
  const spec = RESULT_CARDS[tool.name]
  return spec && spec.accepts(tool.output) ? { component: spec.component, output: tool.output, truncation: truncationOf(tool.output) } : null
}
