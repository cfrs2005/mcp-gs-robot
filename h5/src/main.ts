import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'vant/lib/index.css'
import { migrateLegacyKeys } from './storageKeys'
import './i18n'

migrateLegacyKeys()

createApp(App).use(createPinia()).use(router).mount('#app')
