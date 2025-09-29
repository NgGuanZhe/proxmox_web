import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CloneView from '../views/CloneView.vue' // Import CloneView directly
import SnapshotView from '../views/SnapshotView.vue' // Import SnapshotView directly

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/clone',
      name: 'clone',
      component: CloneView // Use the imported component
    },
    {
      path: '/snapshots',
      name: 'snapshots',
      component: SnapshotView // Use the imported component
    }
  ]
})

export default router
