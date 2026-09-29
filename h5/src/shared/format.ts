import { formatDateTime, formatNumber } from '@/i18n'

/** Upstream timestamps are seconds or milliseconds depending on the endpoint. */
export function toDate(value?: number | null): Date | null {
  if (!value) return null
  const date = new Date(value < 1e11 ? value * 1000 : value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function timestamp(value?: number | null): string {
  const date = toDate(value)
  return date ? formatDateTime(date, { dateStyle: 'medium', timeStyle: 'medium', hour12: false }) : '—'
}

export function shortDateTime(value?: number | null): string {
  const date = toDate(value)
  return date ? formatDateTime(date, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }) : '—'
}

export function clock(date: Date): string {
  return formatDateTime(date, { hour: '2-digit', minute: '2-digit', hour12: false })
}

export function duration(seconds?: number | null): string {
  return seconds == null ? '—' : formatNumber(Math.round(seconds / 60), { style: 'unit', unit: 'minute', unitDisplay: 'long' })
}

export function minutes(seconds?: number | null): string {
  return seconds == null ? '—' : formatNumber(Math.round(seconds / 60), { style: 'unit', unit: 'minute', unitDisplay: 'short' })
}

/** completionPercentage is a 0–1 ratio upstream (0.91 → 91%), unlike batteryPercent which is 0–100. */
export function ratioPercent(value?: number | null): string {
  return value == null ? '—' : formatNumber(value, { style: 'percent', maximumFractionDigits: 0 })
}

export const area = (value?: number | null, digits = 2) => value == null ? '—' : formatNumber(value, { maximumFractionDigits: digits })
