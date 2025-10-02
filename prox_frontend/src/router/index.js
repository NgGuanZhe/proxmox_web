import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CloneView from '../views/CloneView.vue' // Import CloneView directly
import SnapshotView from '../views/SnapshotView.vue' // Import SnapshotView directly
import NetworkView from '../views/NetworkView.vue'
import SdnView from '../views/SdnView.vue'
import LabBuilderView from '../views/LabBuilderView.vue'
import LabPlaygroundView from '../views/LabPlaygroundView.vue'


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
    },
    { path: '/networks', 
      name: 'networks', 
      component: NetworkView
    },
    { path: '/sdn', 
      name: 'sdn', 
      component: SdnView
    },
    { path: '/labbuilder', 
      name: 'labbuilder', 
      component: LabBuilderView
    },
    { path: '/playground', 
      name: 'playground', 
      component: LabPlaygroundView
    }
  ]
})

export default router
