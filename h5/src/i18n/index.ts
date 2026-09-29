// Minimal zero-dependency i18n: one reactive locale, two flat dictionaries, {name} interpolation,
// `.one` / `.other` plurals via Intl.PluralRules, and Intl-based date/number/relative-time formatting.
import { computed, ref } from 'vue'
import { Locale as VantLocale } from 'vant'
import vantEn from 'vant/es/locale/lang/en-US'
import vantZh from 'vant/es/locale/lang/zh-CN'
import { KEYS } from '@/shared/storageKeys'
import en, { type MessageKey, type Messages } from './en'
import zh from './zh'

export type Locale = 'en' | 'zh'
export type { MessageKey }
export const LOCALES: Locale[] = ['en', 'zh']

const dictionaries: Record<Locale, Messages> = { en, zh }
const tags: Record<Locale, string> = { en: 'en-US', zh: 'zh-CN' }
const vant = { en: ['en-US', vantEn], zh: ['zh-CN', vantZh] } as const

function detect(): Locale {
  const saved = localStorage.getItem(KEYS.locale)
  if (saved === 'en' || saved === 'zh') return saved
  return /^zh/i.test(navigator.language || '') ? 'zh' : 'en'
}

export const locale = ref<Locale>(detect())
/** BCP 47 tag for Intl formatters and <html lang>. */
export const localeTag = computed(() => tags[locale.value])

type Params = Record<string, string | number>
const interpolate = (text: string, params?: Params) =>
  params ? text.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match)) : text

export function t(key: MessageKey, params?: Params): string {
  return interpolate(dictionaries[locale.value][key] ?? en[key] ?? key, params)
}

type PluralBase<K = MessageKey> = K extends `${infer B}.one` ? B : never
/** Plural lookup: picks `${base}.one` or `${base}.other`; `{n}` is filled with the locale-formatted count. */
export function tn(base: PluralBase, n: number, params?: Params): string {
  const form = new Intl.PluralRules(localeTag.value).select(n) === 'one' ? 'one' : 'other'
  return t(`${base}.${form}` as MessageKey, { n: formatNumber(n), ...params })
}

export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(localeTag.value, options).format(value)
}

export function formatDateTime(date: Date, options: Intl.DateTimeFormatOptions = { dateStyle: 'medium', timeStyle: 'short', hour12: false }): string {
  return new Intl.DateTimeFormat(localeTag.value, options).format(date)
}

/** Localized "3 minutes ago"; older than a week falls back to a short date. `seconds` is a Unix timestamp. */
export function relativeTime(seconds: number): string {
  const diff = Date.now() / 1000 - seconds
  if (diff < 60) return t('time.justNow')
  const rtf = new Intl.RelativeTimeFormat(localeTag.value, { numeric: 'auto' })
  if (diff < 3600) return rtf.format(-Math.floor(diff / 60), 'minute')
  if (diff < 86400) return rtf.format(-Math.floor(diff / 3600), 'hour')
  if (diff < 604800) return rtf.format(-Math.floor(diff / 86400), 'day')
  return formatDateTime(new Date(seconds * 1000), { month: 'short', day: 'numeric' })
}

function apply() {
  document.documentElement.lang = localeTag.value
  document.title = t('app.title')
  const [name, messages] = vant[locale.value]
  VantLocale.use(name, messages)
}

export function setLocale(next: Locale) {
  locale.value = next
  localStorage.setItem(KEYS.locale, next)
  apply()
}

apply()
