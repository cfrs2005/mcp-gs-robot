// localStorage keys. Renamed from pi.* with the Pi Agent → Saodi rename.
export const KEYS = { apiBase: 'saodi.apiBase', apiKey: 'saodi.apiKey', sessionId: 'saodi.sessionId', locale: 'saodi.locale' } as const

/** One-shot migration: copy each legacy pi.* value to its saodi.* key (new key wins if both exist), then drop the old key. */
export function migrateLegacyKeys(storage: Storage = localStorage): void {
  for (const [name, key] of Object.entries(KEYS)) {
    const legacy = `pi.${name}`
    const value = storage.getItem(legacy)
    if (value === null) continue
    if (storage.getItem(key) === null) storage.setItem(key, value)
    storage.removeItem(legacy)
  }
}
