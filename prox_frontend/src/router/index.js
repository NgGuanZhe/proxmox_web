import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    // --- THIS IS THE NEW ROUTE ---
    {
      path: '/clone',
      name: 'clone',
      // This is a special syntax to lazy-load the page
      component: () => import('../views/CloneView.vue')
    }
  ]
})

export default router
