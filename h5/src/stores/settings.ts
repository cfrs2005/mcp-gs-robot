import { defineStore } from 'pinia'
import { KEYS } from '@/storageKeys'

const read = (key: string) => localStorage.getItem(key) ?? ''

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    apiBase: read(KEYS.apiBase),
    apiKey: read(KEYS.apiKey),
  }),
  actions: {
    save(apiBase: string, apiKey: string) {
      this.apiBase = apiBase.trim().replace(/\/+$/, '')
      this.apiKey = apiKey.trim()
      localStorage.setItem(KEYS.apiBase, this.apiBase)
      localStorage.setItem(KEYS.apiKey, this.apiKey)
    },
  },
})
