import { defineStore } from 'pinia'

const read = (key: string) => localStorage.getItem(key) ?? ''

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    apiBase: read('pi.apiBase'),
    apiKey: read('pi.apiKey'),
  }),
  actions: {
    save(apiBase: string, apiKey: string) {
      this.apiBase = apiBase.trim().replace(/\/+$/, '')
      this.apiKey = apiKey.trim()
      localStorage.setItem('pi.apiBase', this.apiBase)
      localStorage.setItem('pi.apiKey', this.apiKey)
    },
  },
})
