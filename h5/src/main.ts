import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Vant's CSS first, then the design tokens that override its --van-* variables, then the app (App.vue global styles).
import 'vant/lib/index.css'
import './shared/tokens.css'
import App from './App.vue'
import router from './router'
import { migrateLegacyKeys } from './shared/storageKeys'
import './i18n'

migrateLegacyKeys()

createApp(App).use(createPinia()).use(router).mount('#app')
