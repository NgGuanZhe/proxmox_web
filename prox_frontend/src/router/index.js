import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CloneView from '../views/CloneView.vue'
import SnapshotView from '../views/SnapshotView.vue'
import NetworkView from '../views/NetworkView.vue'
import SdnView from '../views/SdnView.vue'
import LabBuilderView from '../views/LabBuilderView.vue'
import LabPlaygroundView from '../views/LabPlaygroundView.vue'
import LoginView from '../views/LoginView.vue' // <-- Import the new Login page

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true } // Mark this page as requiring login
    },
    {
      path: '/clone',
      name: 'clone',
      component: CloneView,
      meta: { requiresAuth: true }
    },
    {
      path: '/snapshots',
      name: 'snapshots',
      component: SnapshotView,
      meta: { requiresAuth: true }
    },
    { 
      path: '/networks', 
      name: 'networks', 
      component: NetworkView,
      meta: { requiresAuth: true }
    },
    { 
      path: '/sdn', 
      name: 'sdn', 
      component: SdnView,
      meta: { requiresAuth: true }
    },
    { 
      path: '/labbuilder', 
      name: 'labbuilder', 
      component: LabBuilderView,
      meta: { requiresAuth: true }
    },
    { 
      path: '/playground', 
      name: 'playground', 
      component: LabPlaygroundView,
      meta: { requiresAuth: true }
    },
    // --- THIS IS THE NEW LOGIN ROUTE ---
    {
      path: '/login',
      name: 'login',
      component: LoginView
      // This page does NOT require auth
    }
  ]
})

// --- THIS IS THE NEW SECURITY GUARD ---
router.beforeEach((to, from, next) => {
  const loggedIn = localStorage.getItem('access_token');

  // If the page requires login AND the user is not logged in
  if (to.meta.requiresAuth && !loggedIn) {
    // Redirect them to the login page
    next({ name: 'login' });
  } else {
    // Otherwise, let them proceed
    next();
  }
});

export default router
