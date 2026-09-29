import { t, type MessageKey } from '@/i18n'

// Codes follow https://developer.gs-robot.com/v3docs/en_US/Robot%20Work%20State%20Reference; names live in the i18n dictionaries.
// Prefer the localized name for a known code; fall back to the backend's enum name, then a generic label.
export function workStateName(status: { work_state_name?: string; workState?: number }): string {
  const code = status.workState
  if (code !== undefined) {
    const key = `workState.${code}` as MessageKey
    const name = t(key)
    if (name !== key) return name
  }
  return status.work_state_name || (code === undefined ? t('workState.unknown') : t('workState.code', { code }))
}
