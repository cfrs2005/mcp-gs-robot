import { createRouter, createWebHashHistory } from 'vue-router'
import ChatView from './views/ChatView.vue'
import RobotsView from './views/RobotsView.vue'
import RobotDetailView from './views/RobotDetailView.vue'
import SettingsView from './views/SettingsView.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    { path: '/chat', component: ChatView },
    { path: '/robots', component: RobotsView },
    { path: '/robots/:sn', component: RobotDetailView },
    { path: '/settings', component: SettingsView },
  ],
})
