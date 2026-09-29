import type { TaskReport } from '@/api/client'
import { formatDateTime } from '@/i18n'
import { toDate } from './format'

export type ReportSummary = { count: number; totalArea: number | null; avgDuration: number | null; avgCompletion: number | null }
export type DayPoint = { key: string; label: string; value: number }

const num = (value: unknown): number | null => typeof value === 'number' && Number.isFinite(value) ? value : null
const mean = (values: (number | null)[]) => {
  const known = values.filter((v): v is number => v !== null)
  return known.length ? known.reduce((a, b) => a + b, 0) / known.length : null
}

/** KPIs over exactly the reports given (a page, not the robot's whole history). Missing fields stay null. */
export function summarize(reports: TaskReport[]): ReportSummary {
  const areas = reports.map(r => num(r.actualCleaningAreaSquareMeter))
  return {
    count: reports.length,
    totalArea: areas.some(a => a !== null) ? areas.reduce<number>((sum, a) => sum + (a ?? 0), 0) : null,
    avgDuration: mean(reports.map(r => num(r.durationSeconds))),
    avgCompletion: mean(reports.map(r => num(r.completionPercentage))),
  }
}

/** Cleaned area per local calendar day (by start time), oldest first, at most `limit` most recent days. */
export function areaByDay(reports: TaskReport[], limit = 7): DayPoint[] {
  const days = new Map<string, DayPoint>()
  for (const report of reports) {
    const date = toDate(report.startTime ?? report.endTime)
    const value = num(report.actualCleaningAreaSquareMeter)
    if (!date || value === null) continue
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    const day = days.get(key) ?? { key, label: formatDateTime(date, { month: 'numeric', day: 'numeric' }), value: 0 }
    day.value += value
    days.set(key, day)
  }
  return [...days.values()].sort((a, b) => a.key.localeCompare(b.key)).slice(-limit)
}

/** Reports newest first. */
export function newest(reports: TaskReport[], n: number): TaskReport[] {
  return [...reports].sort((a, b) => (b.startTime ?? 0) - (a.startTime ?? 0)).slice(0, n)
}
