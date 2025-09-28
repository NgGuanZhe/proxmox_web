<script setup>
import { ref, computed } from 'vue'
import VmCard from '../components/VmCard.vue'
import VmDetailModal from '../components/VmDetailModal.vue'

const vms = ref([])
const isLoading = ref(false)
const error = ref(null)
const selectedVm = ref(null)

// The final, correct grouping logic
const groupedVms = computed(() => {
  const groups = {}
  const templates = []
  const otherVMs = []

  // First, separate templates from all other VMs
  for (const vm of vms.value) {
    if (vm.hardware_details && vm.hardware_details.template === 1) {
      templates.push(vm)
    } else {
      otherVMs.push(vm)
    }
  }

  // Create a group for each template, keyed by the template's name
  for (const template of templates) {
    groups[template.name] = {
      template: template,
      clones: []
    }
  }

  const unassignedVMs = []
  // Go through the non-template VMs and assign them to their parent group
  for (const vm of otherVMs) {
    const description = vm.hardware_details?.description || ''
    const match = description.match(/Cloned from template: (.*)/)
    
    // If we find a match and a group for that template exists...
    if (match && match[1] && groups[match[1].trim()]) {
      // ...add it to that group's clone list
      groups[match[1].trim()].clones.push(vm)
    } else {
      // Otherwise, it's an "other" VM
      unassignedVMs.push(vm)
    }
  }

  // Add the final group for any remaining, unassigned VMs
  if (unassignedVMs.length > 0) {
    groups['Other VMs'] = {
      template: null, // This group has no parent template
      clones: unassignedVMs
    }
  }
  
  return groups
})

async function fetchVMs() {
  isLoading.value = true
  error.value = null
  vms.value = []
  try {
    const response = await fetch('/api/vms')
    if (!response.ok) throw new Error(`Server responded with status: ${response.status}`)
    vms.value = await response.json()
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <header>
    <h1>VM Dashboard</h1>
    <p>A simple interface to view and manage virtual machines.</p>
    <button @click="fetchVMs" :disabled="isLoading">
      {{ isLoading ? 'Loading...' : 'Refresh VM List' }}
    </button>
  </header>

  <main>
    <div v-if="error" class="error-box">
      <p><strong>Error:</strong> {{ error }}</p>
    </div>

    <div class="dashboard-layout">
      <div v-for="(group, groupName) in groupedVms" :key="groupName" class="vm-group-column">
        <h2 class="group-title">{{ groupName }}</h2>
        
        <VmCard v-if="group.template" :vm="group.template" @click="selectedVm = group.template" class="golden-template-card" />

        <div class="vm-grid">
          <VmCard v-for="vm in group.clones" :key="vm.proxmox_id" :vm="vm" @click="selectedVm = vm" />
        </div>
      </div>
    </div>
  </main>

  <VmDetailModal v-if="selectedVm" :vm="selectedVm" @close="selectedVm = null" />
</template>

<style scoped>
header { text-align: center; margin-bottom: 3rem; }
button { background-color: var(--accent-color); color: var(--bg-dark); font-weight: 700; border: none; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; transition: background-color 0.2s; }
.error-box { padding: 1rem; background-color: #ffebee; color: #c62828; border-radius: 5px; text-align: center; }

.dashboard-layout {
  display: flex;
  flex-direction: row;
  gap: 2rem;
  overflow-x: auto;
  padding-bottom: 1rem;
}
.vm-group-column {
  background-color: var(--bg-light);
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  border-radius: 8px;
  min-width: 340px;
  flex-shrink: 0;
}
.group-title {
  color: var(--accent-color);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
  margin-top: 0;
  margin-bottom: 1.5rem;
}
.golden-template-card {
  margin-bottom: 1.5rem;
  border: 2px solid #ffc107;
}
.vm-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}
</style>
